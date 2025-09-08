"""add profile_completed and align enums

Revision ID: add_profile_completed_0001
Revises:
Create Date: 2025-09-07

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_profile_completed_0001"
down_revision = "b8d9e0f1a2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column profile_completed if not exists
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "profile_completed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )

    # Ensure enums exist (no destructive changes; keep existing values)
    # Note: Existing enums ActivityLevel and Goal already created by models; we keep them.


def downgrade() -> None:
    with op.batch_alter_table("user_profiles") as batch_op:
        batch_op.drop_column("profile_completed")
