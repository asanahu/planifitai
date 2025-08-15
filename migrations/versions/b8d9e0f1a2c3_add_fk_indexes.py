"""add fk indexes"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b8d9e0f1a2c3"
down_revision = "f1b6f3a4c8d7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_routines_owner_id", "routines", ["owner_id"], unique=False
    )
    op.create_index(
        "ix_routine_days_routine_id", "routine_days", ["routine_id"], unique=False
    )
    op.create_index(
        "ix_routine_exercises_routine_day_id",
        "routine_exercises",
        ["routine_day_id"],
        unique=False,
    )
    op.create_index(
        "ix_nutrition_meal_items_meal_id",
        "nutrition_meal_items",
        ["meal_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_nutrition_meal_items_meal_id", table_name="nutrition_meal_items"
    )
    op.drop_index(
        "ix_routine_exercises_routine_day_id", table_name="routine_exercises"
    )
    op.drop_index(
        "ix_routine_days_routine_id", table_name="routine_days"
    )
    op.drop_index("ix_routines_owner_id", table_name="routines")
