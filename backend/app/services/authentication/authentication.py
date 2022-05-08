import re
from dataclasses import dataclass, field
from re import Pattern
from typing import AsyncGenerator, Sequence

from fastapi import Depends, Request
from fastapi_users import InvalidPasswordException, UUIDIDMixin
from fastapi_users.authentication import BearerTransport, Transport

from ...core import config
from ...db.session import async_session, get_session
from ...models import user
from .convert import (
    auth_backend_class,
    auth_backend_type,
    fastapi_users_class,
    jwt_strategy_class,
    strategy_class,
    user_db_class,
    user_id_type,
    user_manager_class,
)


async def get_user_db(
    session: async_session = Depends(get_session),
) -> AsyncGenerator[user_db_class[user.user, user_id_type], None]:
    yield user_db_class(session, user.user)


def create_transport() -> Transport:
    return BearerTransport(tokenUrl=config.TOKEN_PREFIX)


def create_strategy() -> strategy_class[user.user, user_id_type]:
    return jwt_strategy_class(  # type: ignore
        secret=str(config.SECRET_KEY),
        lifetime_seconds=config.ACCESS_TOKEN_EXPIRE_SECONDS,
        token_audience=[config.JWT_AUDIENCE],
        algorithm=config.JWT_ALGORITHM,
    )


def create_backend() -> list[auth_backend_type]:
    transport = create_transport()
    return [
        auth_backend_class(
            name=config.AUTH_BACKEND_NAME,
            transport=transport,
            get_strategy=create_strategy,
        )
    ]


class UserManager(UUIDIDMixin, user_manager_class[user.user, user_id_type]):
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
        elif len(password) > self.max_password_length:
            raise InvalidPasswordException(
                reason=f"Password should be at most {self.max_password_length} characters"
            )

        for pattern in self.re_password_deny_list:
            if pattern.search(password):
                raise InvalidPasswordException(
                    reason=f"Password should not include {pattern.pattern}"
                )

        for pattern in self.re_password_need_list:
            if not pattern.search(password):
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
    *backends: auth_backend_type,
) -> fastapi_users_class[user.user, user_id_type]:
    return fastapi_users_class(
        get_user_manager=get_user_manager, auth_backends=backends
    )


@dataclass(frozen=True)
class fastapi_user_class:
    users: fastapi_users_class[user.user, user_id_type]
    named_backends: dict[str, auth_backend_type] = field(default_factory=dict)

    @classmethod
    def init(cls) -> "fastapi_user_class":
        users = create_fastapi_users(*create_backend())
        return cls(users=users)

    @property
    def backends(self) -> Sequence[auth_backend_type]:
        return self.users.authenticator.backends  # type: ignore

    @property
    def get_user_manager(self):
        return self.users.get_user_manager

    def find_backend(self, _val: str, /) -> auth_backend_type:
        for backend in self.backends:
            if backend.name == _val:
                return backend
        raise IndexError(f"there is not auth_backend name: {_val}")

    def get_backend(self, _val: int | str = 0, /) -> auth_backend_type:
        if isinstance(_val, int):
            return self.backends[_val]

        if (backend := self.named_backends.get(_val)) is None:
            backend = self.named_backends[_val] = self.find_backend(_val)
        return backend

    def get_transport(self, _val: int | str = 0, /) -> Transport:
        backend = self.get_backend(_val)
        return backend.transport

    def get_strategy(self, _val: int | str = 0, /):
        backend = self.get_backend(_val)
        return backend.get_strategy
