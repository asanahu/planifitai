"""add equipment column to routine_days

Revision ID: 2025_09_10_0007
Revises: 2025_09_10_0006
Create Date: 2025-09-11 00:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2025_09_10_0007"
down_revision: Union[str, Sequence[str], None] = "2025_09_10_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("routine_days") as batch:
        batch.add_column(sa.Column("equipment", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("routine_days") as batch:
        batch.drop_column("equipment")

