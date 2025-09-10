"""Create routines, routine_days, exercise_catalog, and routine_exercises tables

Revision ID: 7f4dbf4a3e20
Revises: b234998e2f1b
Create Date: 2025-08-13 11:37:41.686420

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f4dbf4a3e20"
down_revision: Union[str, Sequence[str], None] = "b234998e2f1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # routines table
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

    # routine_days table
    op.create_table(
        "routine_days",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("routine_id", sa.Integer(), sa.ForeignKey("routines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.UniqueConstraint("routine_id", "weekday", name="_routine_weekday_uc"),
    )

    # exercise_catalog table (base columns; later migrations may add more)
    op.create_table(
        "exercise_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("equipment", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_exercise_catalog_name", "exercise_catalog", ["name"], unique=True)

    # routine_exercises table
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
    op.drop_index("ix_exercise_catalog_name", table_name="exercise_catalog")
    op.drop_table("exercise_catalog")
    op.drop_table("routine_days")
    op.drop_table("routines")
