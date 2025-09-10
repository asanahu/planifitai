"""Create routines tables if missing (compat fix)

Revision ID: 2025_09_10_0004
Revises: 2025_09_10_0003
Create Date: 2025-09-10 16:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2025_09_10_0004"
down_revision: Union[str, Sequence[str], None] = "2025_09_10_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("routines"):
        op.create_table(
            "routines",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_template", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("active_days", sa.JSON(), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("owner_id", "name", name="_owner_name_uc"),
        )

    if not insp.has_table("routine_days"):
        op.create_table(
            "routine_days",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("routine_id", sa.Integer(), sa.ForeignKey("routines.id", ondelete="CASCADE"), nullable=False),
            sa.Column("weekday", sa.Integer(), nullable=False),
            sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
            sa.UniqueConstraint("routine_id", "weekday", name="_routine_weekday_uc"),
        )

    if not insp.has_table("routine_exercises"):
        op.create_table(
            "routine_exercises",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("routine_day_id", sa.Integer(), sa.ForeignKey("routine_days.id", ondelete="CASCADE"), nullable=False),
            sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercise_catalog.id"), nullable=True),
            sa.Column("exercise_name", sa.String(length=100), nullable=False),
            sa.Column("sets", sa.Integer(), nullable=False),
            sa.Column("reps", sa.Integer(), nullable=True),
            sa.Column("time_seconds", sa.Integer(), nullable=True),
            sa.Column("tempo", sa.String(length=20), nullable=True),
            sa.Column("rest_seconds", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("routine_exercises")
    op.drop_table("routine_days")
    op.drop_table("routines")

