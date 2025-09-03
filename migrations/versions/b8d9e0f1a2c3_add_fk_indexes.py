"""add fk indexes"""

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "b8d9e0f1a2c3"
down_revision = "f1b6f3a4c8d7"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    if "routines" in inspector.get_table_names():
        op.create_index("ix_routines_owner_id", "routines", ["owner_id"], unique=False)

    if "routine_days" in inspector.get_table_names():
        op.create_index(
            "ix_routine_days_routine_id",
            "routine_days",
            ["routine_id"],
            unique=False,
        )

    if "routine_exercises" in inspector.get_table_names():
        op.create_index(
            "ix_routine_exercises_routine_day_id",
            "routine_exercises",
            ["routine_day_id"],
            unique=False,
        )

    if "nutrition_meal_items" in inspector.get_table_names():
        op.create_index(
            "ix_nutrition_meal_items_meal_id",
            "nutrition_meal_items",
            ["meal_id"],
            unique=False,
        )


def downgrade():
    op.drop_index("ix_nutrition_meal_items_meal_id", table_name="nutrition_meal_items")
    op.drop_index("ix_routine_exercises_routine_day_id", table_name="routine_exercises")
    op.drop_index("ix_routine_days_routine_id", table_name="routine_days")
    op.drop_index("ix_routines_owner_id", table_name="routines")
