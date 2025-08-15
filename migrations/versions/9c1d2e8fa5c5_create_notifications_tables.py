"""create notifications tables

Revision ID: 9c1d2e8fa5c5
Revises: 9742803658eb
Create Date: 2025-08-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1d2e8fa5c5"
down_revision: Union[str, Sequence[str], None] = "9742803658eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("tz", sa.String, nullable=False, server_default="UTC"),
        sa.Column(
            "channels_inapp", sa.Boolean, nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "channels_email", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column("quiet_hours_start_local", sa.Time, nullable=True),
        sa.Column("quiet_hours_end_local", sa.Time, nullable=True),
        sa.Column("daily_digest_time_local", sa.Time, nullable=True),
        sa.Column("weekly_digest_weekday", sa.Integer, nullable=True),
        sa.Column("weekly_digest_time_local", sa.Time, nullable=True),
        sa.Column("meal_times_local", sa.JSON, nullable=True),
        sa.Column("water_every_min", sa.Integer, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_notification_pref_user",
        "notification_preferences",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("scheduled_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="scheduled"),
        sa.Column("priority", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("dedupe_key", sa.String(length=128), nullable=True),
        sa.Column("delivered_channels", sa.JSON, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_notifications_user_sched", "notifications", ["user_id", "scheduled_at_utc"]
    )
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_index(
        "ix_notifications_dedupe",
        "notifications",
        ["user_id", "dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_dedupe", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_user_sched", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_notification_pref_user", table_name="notification_preferences")
    op.drop_table("notification_preferences")
