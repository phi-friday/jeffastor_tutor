from enum import Enum

from pydantic import condecimal
from sqlmodel import Field

from .core import base_model, datetime_model, id_model

price_decimal_type = condecimal(max_digits=10, decimal_places=2)


class cleaning_type_enum(str, Enum):
    dust_up = "dust_up"
    spot_clean = "spot_clean"
    full_clean = "full_clean"


class cleaning_base(base_model):
    name: str | None = None
    description: str | None = None
    cleaning_type: cleaning_type_enum = cleaning_type_enum.spot_clean
    price: price_decimal_type | None = None


class cleaning_create(cleaning_base):
    name: str
    price: price_decimal_type


class cleaning_update(cleaning_base):
    cleaning_type: cleaning_type_enum | None = None


class cleanings(id_model, datetime_model, cleaning_base, table=True):
    name: str = Field(index=True)
    cleaning_type: cleaning_type_enum = Field(
        cleaning_type_enum.spot_clean,
        sa_column_kwargs={"server_default": cleaning_type_enum.spot_clean},
    )
    price: price_decimal_type


class cleaning_public(id_model, cleaning_base):
    ...
