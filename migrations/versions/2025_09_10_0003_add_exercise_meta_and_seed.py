"""add exercise meta columns and seed small catalog

Revision ID: 2025_09_10_0003
Revises: 0bebe059a9b5
Create Date: 2025-09-10 00:03:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2025_09_10_0003"
# Dependemos del merge previo y de la creación de tablas de rutinas/catálogo
down_revision: Union[str, Sequence[str], None] = ("0bebe059a9b5", "7f4dbf4a3e20")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # Create table if missing (fresh envs may have applied an older empty migration)
    if not insp.has_table("exercise_catalog"):
        op.create_table(
            "exercise_catalog",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=True),
            sa.Column("equipment", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("level", sa.String(length=20), nullable=True),
            sa.Column("muscle_groups", sa.JSON(), nullable=True),
            sa.Column("media_url", sa.String(length=255), nullable=True),
            sa.Column("demo_url", sa.String(length=255), nullable=True),
        )
        op.create_index("ix_exercise_catalog_name", "exercise_catalog", ["name"], unique=True)
    else:
        # Add enrichment columns if table exists
        with op.batch_alter_table("exercise_catalog") as batch:
            # Add columns only if they don't exist
            # (Some backends don't support IF NOT EXISTS easily, so we try-add)
            try:
                batch.add_column(sa.Column("level", sa.String(length=20), nullable=True))
            except Exception:
                pass
            try:
                batch.add_column(sa.Column("muscle_groups", sa.JSON(), nullable=True))
            except Exception:
                pass
            try:
                batch.add_column(sa.Column("media_url", sa.String(length=255), nullable=True))
            except Exception:
                pass
            try:
                batch.add_column(sa.Column("demo_url", sa.String(length=255), nullable=True))
            except Exception:
                pass

    # Seed a minimal set of exercises if table is empty
    count = conn.execute(sa.text("SELECT COUNT(*) FROM exercise_catalog")).scalar() or 0
    if count == 0:
        rows = [
            {
                "name": "Push Up",
                "category": "pecho",
                "equipment": "peso corporal",
                "description": "Flexiones básicas.",
                "level": "beginner",
                "muscle_groups": ["pecho", "tríceps"],
                "media_url": None,
                "demo_url": "https://example.com/pushup.gif",
            },
            {
                "name": "Sentadilla",
                "category": "piernas",
                "equipment": "peso corporal",
                "description": "Sentadilla con peso corporal.",
                "level": "beginner",
                "muscle_groups": ["cuádriceps", "glúteos"],
                "media_url": None,
                "demo_url": "https://example.com/squat.gif",
            },
            {
                "name": "Remo con mancuernas",
                "category": "espalda",
                "equipment": "mancuernas",
                "description": "Remo a una mano.",
                "level": "intermediate",
                "muscle_groups": ["dorsales", "bíceps"],
                "media_url": None,
                "demo_url": "https://example.com/row.gif",
            },
        ]
        meta = sa.MetaData()
        t = sa.Table(
            "exercise_catalog",
            meta,
            sa.Column("id", sa.Integer),
            sa.Column("name", sa.String(100)),
            sa.Column("category", sa.String(50)),
            sa.Column("equipment", sa.String(100)),
            sa.Column("description", sa.Text()),
            sa.Column("level", sa.String(20)),
            sa.Column("muscle_groups", sa.JSON()),
            sa.Column("media_url", sa.String(255)),
            sa.Column("demo_url", sa.String(255)),
        )
        op.bulk_insert(t, rows)


def downgrade() -> None:
    # Only drop columns; we won't remove seeded rows in downgrade
    with op.batch_alter_table("exercise_catalog") as batch:
        batch.drop_column("demo_url")
        batch.drop_column("media_url")
        batch.drop_column("muscle_groups")
        batch.drop_column("level")
