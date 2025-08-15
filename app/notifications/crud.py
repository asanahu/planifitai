from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from . import models, schemas


def get_preferences(db: Session, user_id: int) -> models.NotificationPreference:
    pref = db.execute(
        select(models.NotificationPreference).where(
            models.NotificationPreference.user_id == user_id
        )
    ).scalar_one_or_none()
    return pref


def upsert_preferences(
    db: Session, user_id: int, data: schemas.NotificationPreferencesUpdate
) -> models.NotificationPreference:
    pref = get_preferences(db, user_id)
    if not pref:
        pref = models.NotificationPreference(user_id=user_id)
        db.add(pref)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)
    db.commit()
    db.refresh(pref)
    return pref


def create_notification(
    db: Session, notif: schemas.NotificationCreate
) -> models.Notification:
    if notif.dedupe_key:
        existing = db.execute(
            select(models.Notification).where(
                models.Notification.user_id == notif.user_id,
                models.Notification.dedupe_key == notif.dedupe_key,
            )
        ).scalar_one_or_none()
        if existing:
            return existing
    db_obj = models.Notification(
        user_id=notif.user_id,
        category=notif.category,
        type=notif.type,
        title=notif.title,
        body=notif.body,
        payload=notif.payload,
        scheduled_at_utc=notif.scheduled_at_utc,
        dedupe_key=notif.dedupe_key,
        priority=notif.priority,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def list_notifications(
    db: Session,
    user_id: int,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = select(models.Notification).where(models.Notification.user_id == user_id)
    if status == "unread":
        stmt = stmt.where(models.Notification.read_at_utc.is_(None))
    elif status:
        stmt = stmt.where(models.Notification.status == status)
    stmt = (
        stmt.order_by(models.Notification.scheduled_at_utc.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars())


def mark_read(db: Session, notif: models.Notification) -> models.Notification:
    notif.read_at_utc = datetime.utcnow()
    db.commit()
    db.refresh(notif)
    return notif


def mark_dismissed(db: Session, notif: models.Notification) -> models.Notification:
    notif.dismissed_at_utc = datetime.utcnow()
    db.commit()
    db.refresh(notif)
    return notif


def get_notification(
    db: Session, user_id: int, notif_id: int
) -> models.Notification | None:
    return db.execute(
        select(models.Notification).where(
            models.Notification.id == notif_id, models.Notification.user_id == user_id
        )
    ).scalar_one_or_none()
