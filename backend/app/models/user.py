from typing import TypeVar, cast
from uuid import uuid4

from fastapi_users import models
from pydantic import UUID4, EmailStr
from pydantic import Field as _Field
from sqlmodel import Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select

from .core import base_model, datetime_model

min_name_length = 4
max_name_length = 20

_T = TypeVar("_T", bound="user")


class user_base(models.BaseUser, datetime_model):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_create(models.BaseUserCreate):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_update(models.BaseUserUpdate):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_read(user_base):
    ...


class user(base_model, user_base, models.BaseUserDB, table=True):
    __tablename__: str = "users"

    id: UUID4 = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(min_length=min_name_length, max_length=max_name_length)
    hashed_password: str = Field(max_length=2**10)
    email: EmailStr = Field(index=True)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    @classmethod
    async def get_from_email(
        cls: type[_T], session: AsyncSession, email: str
    ) -> _T | None:
        is_user_cur = await session.exec(
            cast(Select[_T], select(cls).where(cls.email == email))
        )
        return is_user_cur.first()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate(self)
