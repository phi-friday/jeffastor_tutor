from uuid import uuid4

from fastapi_users import models
from pydantic import UUID4, EmailStr
from pydantic import Field as _Field
from sqlmodel import Field

from .core import base_model, datetime_model

min_name_length = 4
max_name_length = 20


class user_base(models.BaseUser, datetime_model):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_create(models.BaseUserCreate):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_update(models.BaseUserUpdate):
    name: str = _Field(min_length=min_name_length, max_length=max_name_length)


class user_read(user_base):
    ...


class user(user_base, models.BaseUserDB):
    ...


class user_model(base_model, datetime_model, table=True):
    __tablename__: str = "users"

    id: UUID4 = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(min_length=min_name_length, max_length=max_name_length)
    hashed_password: str = Field(max_length=2**10)
    email: EmailStr = Field(sa_column_kwargs={"unique": True})
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
