from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Dict
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from . import crud, models, schemas

DEFAULT_TZ = "Europe/Madrid"


def _tz(pref: models.NotificationPreference | None) -> str:
    return pref.tz if pref and pref.tz else DEFAULT_TZ


def _combine_to_utc(day: date, t: time, tz: str) -> datetime:
    local = datetime.combine(day, t)
    local = local.replace(tzinfo=ZoneInfo(tz))
    return local.astimezone(ZoneInfo("UTC"))


def _respect_quiet_hours(
    pref: models.NotificationPreference, local_dt: datetime
) -> datetime:
    if not pref or not pref.quiet_hours_start_local or not pref.quiet_hours_end_local:
        return local_dt
    tz = ZoneInfo(pref.tz or DEFAULT_TZ)
    start = datetime.combine(local_dt.date(), pref.quiet_hours_start_local, tz)
    end = datetime.combine(local_dt.date(), pref.quiet_hours_end_local, tz)
    if pref.quiet_hours_start_local < pref.quiet_hours_end_local:
        if start <= local_dt < end:
            return end
    else:
        if local_dt >= start or local_dt < end:
            if local_dt >= start:
                return end + timedelta(days=1)
            else:
                return end
    return local_dt


def schedule_routine_notifications(
    db: Session,
    user_id: int,
    routine_id: int,
    active_days: Dict[str, bool],
    hour_local: time,
) -> list[models.Notification]:
    pref = crud.get_preferences(db, user_id)
    tz = _tz(pref)
    today = date.today()
    created = []
    for i in range(7):
        day = today + timedelta(days=i)
        weekday = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][day.weekday()]
        if not active_days.get(weekday):
            continue
        local_dt = datetime.combine(day, hour_local, tzinfo=ZoneInfo(tz))
        local_dt = _respect_quiet_hours(pref, local_dt)
        scheduled = local_dt.astimezone(ZoneInfo("UTC"))
        dedupe_key = f"workout:{user_id}:{routine_id}:{day.isoformat()}"
        notif = schemas.NotificationCreate(
            user_id=user_id,
            category=models.NotificationCategory.ROUTINE,
            type=models.NotificationType.WORKOUT_REMINDER,
            title="Workout Reminder",
            body=f"Routine {routine_id}",
            payload={"routine_id": routine_id},
            scheduled_at_utc=scheduled,
            dedupe_key=dedupe_key,
        )
        created.append(crud.create_notification(db, notif))
    return created


def schedule_nutrition_reminders(
    db: Session,
    user_id: int,
    meal_times_local: Dict[str, str] | None,
    water_every_min: int | None,
) -> list[models.Notification]:
    pref = crud.get_preferences(db, user_id)
    tz = _tz(pref)
    today = date.today()
    created = []
    if meal_times_local:
        for meal, t_str in meal_times_local.items():
            hour, minute = map(int, t_str.split(":"))
            t = time(hour, minute)
            local_dt = datetime.combine(today, t, tzinfo=ZoneInfo(tz))
            local_dt = _respect_quiet_hours(pref, local_dt)
            scheduled = local_dt.astimezone(ZoneInfo("UTC"))
            dedupe_key = f"meal:{user_id}:{meal}:{today.isoformat()}"
            notif = schemas.NotificationCreate(
                user_id=user_id,
                category=models.NotificationCategory.NUTRITION,
                type=models.NotificationType.MEAL_REMINDER,
                title=f"{meal.title()} Reminder",
                body="Time to eat",
                payload={"meal": meal},
                scheduled_at_utc=scheduled,
                dedupe_key=dedupe_key,
            )
            created.append(crud.create_notification(db, notif))
    if water_every_min:
        local_dt = datetime.now(tz=ZoneInfo(tz)) + timedelta(minutes=water_every_min)
        local_dt = _respect_quiet_hours(pref, local_dt)
        scheduled = local_dt.astimezone(ZoneInfo("UTC"))
        dedupe_key = f"water:{user_id}:{today.isoformat()}"
        notif = schemas.NotificationCreate(
            user_id=user_id,
            category=models.NotificationCategory.NUTRITION,
            type=models.NotificationType.WATER_REMINDER,
            title="Water Reminder",
            body="Drink water",
            payload=None,
            scheduled_at_utc=scheduled,
            dedupe_key=dedupe_key,
        )
        created.append(crud.create_notification(db, notif))
    return created


def dispatch_notification(db: Session, notif_id: int) -> models.Notification | None:
    """Mark a notification as sent and record delivered channels."""
    notif = db.get(models.Notification, notif_id)
    if not notif:
        return None
    delivered = []
    pref = crud.get_preferences(db, notif.user_id)
    if pref.channels_inapp:
        delivered.append("inapp")
    if pref.channels_email:
        delivered.append("email")
    notif.status = models.NotificationStatus.SENT
    notif.sent_at_utc = datetime.utcnow()
    notif.delivered_channels = delivered
    db.commit()
    db.refresh(notif)
    return notif
