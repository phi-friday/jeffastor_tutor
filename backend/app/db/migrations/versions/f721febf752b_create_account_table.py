"""create account table

Revision ID: f721febf752b
Revises: 
Create Date: 2022-04-27 17:21:25.945460

"""
import sys
from pathlib import Path

import sqlalchemy as sa
from alembic import op

sys.path.append(Path(__file__).resolve().parents[4].as_posix())
from app.models.cleaning import cleanings
from app.models.core import datetime_model
from app.models.user import user

# revision identifiers, used by Alembic.
revision = "f721febf752b"
down_revision = None
branch_labels = None
depends_on = None

cleanings_table = cleanings.get_table()
users_table = user.get_table()


def create_cleanings_table() -> None:
    col_names = {"id", "name", "description", "cleaning_type", "price"}.union(
        datetime_model.datetime_attrs
    )

    op.create_table(
        cleanings_table.name,
        *[col for col in cleanings_table.columns if col.name in col_names]
    )


def create_user_table() -> None:
    col_names = {
        "id",
        "name",
        "hashed_password",
        "email",
        "is_active",
        "is_superuser",
        "is_verified",
    }.union(datetime_model.datetime_attrs)

    op.create_table(
        users_table.name, *[col for col in users_table.columns if col.name in col_names]
    )


def upgrade():
    create_cleanings_table()
    create_user_table()


def downgrade():
    op.drop_table(cleanings_table.name)
    op.drop_table(users_table.name)
