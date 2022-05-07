from datetime import datetime
from typing import Any, TypeVar, cast
from uuid import uuid4

from pydantic import UUID4
from sqlmodel import Field, SQLModel, Table

_T = TypeVar("_T", bound=SQLModel)
_D = TypeVar("_D", bound="datetime_model")


class fix_return_type_model(SQLModel):
    """
    sqlmodel에서 parse_obj 리턴값 정상적으로 수정하기 전까지 사용
    +
    validate 또한 같은 문제 있음
    """

    @classmethod
    def parse_obj(cls: type[_T], obj: Any, update: dict[str, Any] | None = None) -> _T:
        return cast(_T, super().parse_obj(obj, update))

    @classmethod
    def validate(cls: type[_T], value: Any) -> _T:
        return cast(_T, super().validate(value))


class base_model(fix_return_type_model):
    @classmethod
    def get_table(cls) -> Table:
        if (table := getattr(cls, "__table__", None)) is None:
            raise ValueError("not table")
        return table


class id_model(fix_return_type_model):
    @classmethod
    @property
    def id_type(cls) -> Any:
        return cls.__fields__["id"].type_


class int_id_model(id_model):
    id: int | None = Field(None, primary_key=True)


class uuid_id_model(id_model):
    id: UUID4 | None = Field(default_factory=uuid4, primary_key=True)


class datetime_model(fix_return_type_model):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update(self: _D) -> _D:
        self.updated_at = datetime.now()
        return self

    @classmethod
    @property
    def datetime_attrs(cls) -> set[str]:
        return set(datetime_model.__fields__.keys())
