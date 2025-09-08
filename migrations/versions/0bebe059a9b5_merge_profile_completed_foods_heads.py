"""merge profile_completed + foods heads

Revision ID: 0bebe059a9b5
Revises: add_profile_completed_0001, 2025_09_08_0002
Create Date: 2025-09-08 20:32:42.554601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bebe059a9b5'
down_revision: Union[str, Sequence[str], None] = ('add_profile_completed_0001', '2025_09_08_0002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
