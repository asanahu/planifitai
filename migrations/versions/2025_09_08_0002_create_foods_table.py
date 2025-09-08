"""create foods table for nutrition cache

Revision ID: 2025_09_08_0002
Revises: e1a1c2d3e4f5
Create Date: 2025-09-08 00:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2025_09_08_0002"
down_revision = "e1a1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure a clean enum state on Postgres in case of partial runs
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS foodsource")

    op.create_table(
        "foods",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("source", sa.Enum("fdc", "bedca", name="foodsource"), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(10, 2), nullable=True),
        sa.Column("protein_g", sa.Numeric(10, 2), nullable=True),
        sa.Column("carbs_g", sa.Numeric(10, 2), nullable=True),
        sa.Column("fat_g", sa.Numeric(10, 2), nullable=True),
        sa.Column("portion_suggestions", sa.JSON(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("lang", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("source", "source_id", name="uix_food_source_source_id"),
    )
    op.create_index("ix_food_name", "foods", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_food_name", table_name="foods")
    op.drop_table("foods")
    # drop enum type on postgres
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS foodsource")
