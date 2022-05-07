from typing import TypeVar

from fastapi_users import schemas
from pydantic import EmailStr
from pydantic import Field as _Field
from sqlmodel import Field, select

from ..db.session import async_session
from .core import base_model, datetime_model, id_model

min_name_length = 4
max_name_length = 20


_T = TypeVar("_T", bound="user")
user_id_type = int


class user(id_model, datetime_model, base_model, table=True):
    __tablename__: str = "users"

    name: str = Field(min_length=min_name_length, max_length=max_name_length)
    hashed_password: str = Field(max_length=2**10)
    email: EmailStr = Field(index=True)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    @classmethod
    async def get_from_email(
        cls: type[_T], session: async_session, email: str
    ) -> _T | None:
        is_user_cur = await session.exec(select(cls).where(cls.email == email))
        return is_user_cur.first()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate(self)


class user_read(schemas.BaseUser[user_id_type], datetime_model):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_create(schemas.BaseUserCreate):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_update(schemas.BaseUserUpdate):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)
