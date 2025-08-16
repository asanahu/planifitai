from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .models import NotificationCategory, NotificationStatus, NotificationType


class NotificationPreferencesBase(BaseModel):
    tz: str = "UTC"
    channels_inapp: bool = True
    channels_email: bool = False
    quiet_hours_start_local: Optional[time] = None
    quiet_hours_end_local: Optional[time] = None
    daily_digest_time_local: Optional[time] = None
    weekly_digest_weekday: Optional[int] = None
    weekly_digest_time_local: Optional[time] = None
    meal_times_local: Optional[Dict[str, str]] = None
    water_every_min: Optional[int] = None


class NotificationPreferences(NotificationPreferencesBase):
    id: int

    class Config:
        orm_mode = True


class NotificationPreferencesUpdate(NotificationPreferencesBase):
    pass


class NotificationBase(BaseModel):
    user_id: int
    category: NotificationCategory
    type: NotificationType
    title: str
    body: str
    payload: Optional[Dict[str, Any]] = None
    scheduled_at_utc: datetime
    priority: int = 0
    dedupe_key: Optional[str] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationOut(BaseModel):
    id: int
    category: NotificationCategory
    type: NotificationType
    title: str
    body: str
    payload: Optional[Dict[str, Any]]
    scheduled_at_utc: datetime
    sent_at_utc: Optional[datetime]
    read_at_utc: Optional[datetime]
    dismissed_at_utc: Optional[datetime]
    status: NotificationStatus
    delivered_channels: Optional[List[str]]

    class Config:
        orm_mode = True
