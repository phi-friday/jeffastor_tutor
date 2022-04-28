"""create account table

Revision ID: f721febf752b
Revises: 
Create Date: 2022-04-27 17:21:25.945460

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f721febf752b'
down_revision = None
branch_labels = None
depends_on = None

def create_cleanings_table() -> None:
    import sys
    from pathlib import Path
    sys.path.append(Path(__file__).resolve().parents[4].as_posix())
    from app.models.cleaning import cleanings

    table = cleanings.get_table()

    op.create_table(
        table.name,
        *table.columns
    )

def upgrade():
    create_cleanings_table()


def downgrade():
    op.drop_table('cleanings')
