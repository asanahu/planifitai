"""merge routines+nutrition heads

Revision ID: 9742803658eb
Revises: 123456789abc, d1a5f8bda1a6
Create Date: 2025-08-13 16:24:50.729620

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "9742803658eb"
down_revision: Union[str, Sequence[str], None] = ("123456789abc", "d1a5f8bda1a6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
