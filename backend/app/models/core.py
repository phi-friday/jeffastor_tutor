from typing import Any, TypeVar, cast

from sqlmodel import Field, SQLModel, Table

_T = TypeVar("_T", bound=SQLModel)


class fix_parse_obj_model(SQLModel):
    """
    sqlmodel에서 parse_obj 리턴값 정상적으로 수정하기 전까지 사용
    """

    @classmethod
    def parse_obj(cls: type[_T], obj: Any, update: dict[str, Any] | None = None) -> _T:
        return cast(_T, super().parse_obj(obj, update))


class base_model(fix_parse_obj_model):
    @classmethod
    def get_table(cls) -> Table:
        if (table := getattr(cls, "__table__", None)) is None:
            raise ValueError("not table")
        return table


class id_model(fix_parse_obj_model):
    id: int | None = Field(None, primary_key=True)
