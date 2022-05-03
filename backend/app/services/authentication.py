from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
    Strategy,
    Transport,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core import config
from ..db.session import get_session
from ..models.user import user, user_base, user_create, user_model, user_update


async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(user, session, user_model)  # type: ignore


def create_transport() -> Transport:
    return BearerTransport(tokenUrl=config.TOKEN_PREFIX)


def create_strategy() -> Strategy:
    return JWTStrategy(
        secret=str(config.SECRET_KEY),
        lifetime_seconds=3600,
    )


def create_backend() -> list[AuthenticationBackend]:
    transport = create_transport()
    return [
        AuthenticationBackend(
            name="bearer_jwt", transport=transport, get_strategy=create_strategy
        )
    ]


class UserManager(BaseUserManager[user_create, user]):
    user_db_model = user
    reset_password_token_secret = str(config.SECRET_KEY)
    verification_token_secret = str(config.SECRET_KEY)

    async def on_after_register(self, user: user, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: user, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: user, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


def create_fastapi_users(*backends: AuthenticationBackend) -> FastAPIUsers:
    return FastAPIUsers(
        get_user_manager=get_user_manager,
        auth_backends=backends,
        user_model=user_base,
        user_create_model=user_create,
        user_update_model=user_update,
        user_db_model=user,
    )


@dataclass(frozen=True)
class fastapi_user:
    users: FastAPIUsers
    backends: list[AuthenticationBackend]

    @classmethod
    def init(cls) -> "fastapi_user":
        backends = create_backend()
        users = create_fastapi_users(*backends)
        return cls(users=users, backends=backends)
