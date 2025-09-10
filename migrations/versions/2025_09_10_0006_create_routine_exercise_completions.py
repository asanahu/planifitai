"""create routine_exercise_completions table

Revision ID: 2025_09_10_0006
Revises: 2025_09_10_0005
Create Date: 2025-09-10 23:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2025_09_10_0006"
down_revision: Union[str, Sequence[str], None] = "2025_09_10_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routine_exercise_completions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "routine_exercise_id",
            sa.Integer(),
            sa.ForeignKey("routine_exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "routine_exercise_id", "date", name="uix_user_exercise_date"),
    )
    op.create_index(
        op.f("ix_routine_exercise_completions_user_id"),
        "routine_exercise_completions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_routine_exercise_completions_user_id"), table_name="routine_exercise_completions")
    op.drop_table("routine_exercise_completions")

