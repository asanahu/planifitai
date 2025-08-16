"""add content embeddings table

Revision ID: e1a1c2d3e4f5
Revises: 9c1d2e8fa5c5
Create Date: 2024-08-14 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "9c1d2e8fa5c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("namespace", sa.String(length=50), nullable=False),
        sa.Column("ref_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_embeddings_namespace_ref",
        "content_embeddings",
        ["namespace", "ref_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_embeddings_namespace_ref", table_name="content_embeddings"
    )
    op.drop_table("content_embeddings")
