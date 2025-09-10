"""expand progressmetric enum with workout and nutrition metrics

Revision ID: 2025_09_10_0005
Revises: 2025_09_10_0004
Create Date: 2025-09-10 22:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2025_09_10_0005"
down_revision: Union[str, Sequence[str], None] = "2025_09_10_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing enum values to progressmetric for Postgres backends.

    Adds: workout, calories_intake, protein_g, carbs_g, fat_g, water_ml
    """
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # Only needed for Postgres; other backends (e.g., SQLite) don't need enum alteration
        return

    # Use IF NOT EXISTS to make this idempotent across environments
    for val in [
        "workout",
        "calories_intake",
        "protein_g",
        "carbs_g",
        "fat_g",
        "water_ml",
    ]:
        op.execute(sa.text(f"ALTER TYPE progressmetric ADD VALUE IF NOT EXISTS '{val}'"))


def downgrade() -> None:
    # Postgres cannot remove enum values easily; keep as no-op.
    pass

