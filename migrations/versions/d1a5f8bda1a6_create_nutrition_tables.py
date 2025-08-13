"""create nutrition tables

Revision ID: d1a5f8bda1a6
Revises: b234998e2f1b
Create Date: 2025-08-13 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1a5f8bda1a6"
down_revision: Union[str, Sequence[str], None] = "b234998e2f1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nutrition_meals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "meal_type",
            sa.Enum("breakfast", "lunch", "dinner", "snack", "other", name="mealtype"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_nutrition_meals_user_date", "nutrition_meals", ["user_id", "date"], unique=False
    )

    op.create_table(
        "nutrition_meal_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=True),
        sa.Column("food_name", sa.String(length=255), nullable=True),
        sa.Column("serving_qty", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "serving_unit",
            sa.Enum("g", "ml", "unit", name="servingunit"),
            nullable=False,
        ),
        sa.Column("calories_kcal", sa.Numeric(10, 2), nullable=False),
        sa.Column("protein_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("fiber_g", sa.Numeric(10, 2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(10, 2), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(10, 2), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["meal_id"], ["nutrition_meals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "nutrition_water_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("datetime_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("volume_ml", sa.Integer(), nullable=False),
        sa.Column(
            "source",
            sa.Enum("manual", "app", "wearable", name="watersource"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "nutrition_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("calories_target", sa.Integer(), nullable=False),
        sa.Column("protein_g_target", sa.Numeric(10, 2), nullable=False),
        sa.Column("carbs_g_target", sa.Numeric(10, 2), nullable=False),
        sa.Column("fat_g_target", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "source", sa.Enum("auto", "custom", name="targetsource"), nullable=False
        ),
        sa.Column("method", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="uix_target_user_date"),
    )
    op.create_index(
        "ix_nutrition_targets_user_date",
        "nutrition_targets",
        ["user_id", "date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_nutrition_targets_user_date", table_name="nutrition_targets")
    op.drop_table("nutrition_targets")
    op.drop_table("nutrition_water_logs")
    op.drop_table("nutrition_meal_items")
    op.drop_index("ix_nutrition_meals_user_date", table_name="nutrition_meals")
    op.drop_table("nutrition_meals")
