from pydantic import condecimal
from sqlmodel import Field

from .base import base_model


class cleanings(base_model, table=True):
    id: int | None = Field(None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    cleaning_type: str = Field(
        (_default_cleaning_type := "spot_clean"),
        sa_column_kwargs={"server_default": _default_cleaning_type},
    )
    price: condecimal(max_digits=10, decimal_places=2)  # type: ignore
