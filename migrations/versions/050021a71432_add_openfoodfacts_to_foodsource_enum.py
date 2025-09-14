"""Add openfoodfacts to FoodSource enum

Revision ID: 050021a71432
Revises: 2025_09_11_0008
Create Date: 2025-09-12 01:11:18.346974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '050021a71432'
down_revision: Union[str, Sequence[str], None] = '2025_09_11_0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'openfoodfacts' to FoodSource enum for PostgreSQL
    # SQLite doesn't support ALTER TYPE, so we'll skip it for SQLite
    try:
        op.execute("ALTER TYPE foodsource ADD VALUE 'openfoodfacts'")
    except Exception:
        # If it fails (e.g., SQLite), that's OK - the enum is handled at Python level
        pass


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require recreating the enum type and updating all references
    # For now, we'll leave the enum value in place
    pass
