"""encrypt PHI columns"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1b6f3a4c8d7"  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = "e1a1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.alter_column(
            "weight_kg", type_=sa.LargeBinary(), existing_nullable=True
        )
        batch_op.alter_column(
            "height_cm", type_=sa.LargeBinary(), existing_nullable=True
        )
        batch_op.add_column(
            sa.Column("medical_conditions", sa.LargeBinary(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_column("medical_conditions")
        batch_op.alter_column("height_cm", type_=sa.Float(), existing_nullable=True)
        batch_op.alter_column("weight_kg", type_=sa.Float(), existing_nullable=True)
