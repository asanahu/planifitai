from __future__ import annotations

from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationCategory(str, Enum):
    ROUTINE = "routine"
    NUTRITION = "nutrition"
    PROGRESS = "progress"
    SYSTEM = "system"


class NotificationType(str, Enum):
    WORKOUT_REMINDER = "workout_reminder"
    MEAL_REMINDER = "meal_reminder"
    WATER_REMINDER = "water_reminder"
    WEIGH_IN = "weigh_in"
    PROGRESS_DAILY = "progress_daily"
    PROGRESS_WEEKLY = "progress_weekly"
    CUSTOM = "custom"


class NotificationStatus(str, Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    tz = Column(String, nullable=False, default="UTC")
    channels_inapp = Column(Boolean, nullable=False, default=True)
    channels_email = Column(Boolean, nullable=False, default=False)
    quiet_hours_start_local = Column(Time, nullable=True)
    quiet_hours_end_local = Column(Time, nullable=True)
    daily_digest_time_local = Column(Time, nullable=True)
    weekly_digest_weekday = Column(Integer, nullable=True)
    weekly_digest_time_local = Column(Time, nullable=True)
    meal_times_local = Column(JSON, nullable=True)
    water_every_min = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category = Column(SAEnum(NotificationCategory), nullable=False)
    type = Column(SAEnum(NotificationType), nullable=False)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)
    scheduled_at_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    sent_at_utc = Column(DateTime(timezone=True), nullable=True)
    read_at_utc = Column(DateTime(timezone=True), nullable=True)
    dismissed_at_utc = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(NotificationStatus), nullable=False, default=NotificationStatus.SCHEDULED)
    priority = Column(SmallInteger, nullable=False, default=0)
    dedupe_key = Column(String(128), nullable=True)
    delivered_channels = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_notifications_user_sched", "user_id", "scheduled_at_utc"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_dedupe", "user_id", "dedupe_key", unique=True),
    )
