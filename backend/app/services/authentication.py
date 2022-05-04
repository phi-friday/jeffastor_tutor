import re
from dataclasses import dataclass
from re import Pattern
from typing import AsyncGenerator, Sequence

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, InvalidPasswordException
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
    Strategy,
    Transport,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core import config
from ..db.session import get_session
from ..models import user

user_manager_type = BaseUserManager[user.user_create, user.user]
strategy_type = Strategy[user.user_create, user.user]


class token_model(BaseModel):
    access_token: str
    token_type: str = "bearer"

    @classmethod
    def from_token(cls, token: str) -> "token_model":
        return cls(access_token=token)


async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(user.user, session, user.user_model)  # type: ignore


def create_transport() -> Transport:
    return BearerTransport(tokenUrl=config.TOKEN_PREFIX)


def create_strategy() -> Strategy[user.user_create, user.user]:
    return JWTStrategy(secret=str(config.SECRET_KEY), lifetime_seconds=3600)


def create_backend() -> list[AuthenticationBackend[user.user_create, user.user]]:
    transport = create_transport()
    return [
        AuthenticationBackend(
            name="bearer_jwt", transport=transport, get_strategy=create_strategy
        )
    ]


class UserManager(BaseUserManager[user.user_create, user.user]):
    user_db_model = user.user
    reset_password_token_secret = str(config.SECRET_KEY)
    verification_token_secret = str(config.SECRET_KEY)

    min_password_length: int = 10
    max_password_length: int = 30
    re_password_need_list: list[Pattern] = [
        re.compile(r"[a-zA-Z]"),
        re.compile(r"[0-9]"),
        re.compile(r"[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"]"),
    ]
    re_password_deny_list: list[Pattern] = []

    async def validate_password(
        self, password: str, user: user.user_create | user.user
    ) -> None:
        if len(password) < self.min_password_length:
            raise InvalidPasswordException(
                reason=f"Password should be at least {self.min_password_length} characters"
            )
        elif len(password) > self.min_password_length:
            raise InvalidPasswordException(
                reason=f"Password should be at most {self.max_password_length} characters"
            )

        for pattern in self.re_password_deny_list:
            if pattern.match(password):
                raise InvalidPasswordException(
                    reason=f"Password should not include {pattern.pattern}"
                )

        for pattern in self.re_password_need_list:
            if not pattern.match(password):
                raise InvalidPasswordException(
                    reason=f"Password must include {pattern.pattern}"
                )

    async def on_after_register(self, user: user.user, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: user.user, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: user.user, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


def create_fastapi_users(
    *backends: AuthenticationBackend[user.user_create, user.user],
) -> FastAPIUsers[user.user_base, user.user_create, user.user_update, user.user]:
    return FastAPIUsers(
        get_user_manager=get_user_manager,
        auth_backends=backends,
        user_model=user.user_base,
        user_create_model=user.user_create,
        user_update_model=user.user_update,
        user_db_model=user.user,
    )


@dataclass(frozen=True)
class fastapi_user_class:
    users: FastAPIUsers[user.user_base, user.user_create, user.user_update, user.user]

    @classmethod
    def init(cls) -> "fastapi_user_class":
        users = create_fastapi_users(*create_backend())
        return cls(users=users)

    @property
    def backends(self) -> Sequence[AuthenticationBackend[user.user_create, user.user]]:
        return self.users.authenticator.backends

    @property
    def user_manager_depends(self) -> user_manager_type:
        return Depends(self.users.get_user_manager)

    def strategy_depends(self, num: int = 0, /) -> strategy_type:
        backend = self.backends[num]
        return Depends(backend.get_strategy)
