"""expand user profile fields

Revision ID: 2025_09_11_0008
Revises: 2025_09_10_0007
Create Date: 2025-09-11 07:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2025_09_11_0008"
down_revision: Union[str, Sequence[str], None] = "2025_09_10_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch:
        batch.add_column(sa.Column("first_name", sa.String(), nullable=True))
        batch.add_column(sa.Column("last_name", sa.String(), nullable=True))
        batch.add_column(sa.Column("sex", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("training_days_per_week", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("time_per_session_min", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("equipment_access", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("dietary_preference", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("allergies", sa.LargeBinary(), nullable=True))

    op.create_index("ix_user_profiles_first_name", "user_profiles", ["first_name"], unique=False)
    op.create_index("ix_user_profiles_last_name", "user_profiles", ["last_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_profiles_last_name", table_name="user_profiles")
    op.drop_index("ix_user_profiles_first_name", table_name="user_profiles")

    with op.batch_alter_table("user_profiles") as batch:
        batch.drop_column("allergies")
        batch.drop_column("dietary_preference")
        batch.drop_column("equipment_access")
        batch.drop_column("time_per_session_min")
        batch.drop_column("training_days_per_week")
        batch.drop_column("sex")
        batch.drop_column("last_name")
        batch.drop_column("first_name")

