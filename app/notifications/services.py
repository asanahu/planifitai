from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Dict
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import crud, models, schemas

DEFAULT_TZ = "Europe/Madrid"


class ScheduleResult(dict):
    """Wrapper result for scheduling operations.

    Acts like a ``dict`` for JSON serialization while ``len(result)``
    returns the number of notifications created, keeping backward
    compatibility with Celery tasks that expect a sequence-like object.
    """

    def __init__(self, notifications: list[models.Notification]):
        super().__init__({"scheduled_count": len(notifications)})
        self._notifications = notifications

    def __len__(self) -> int:  # pragma: no cover - simple delegation
        return len(self._notifications)


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
) -> ScheduleResult:
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
    return ScheduleResult(created)


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
    
    # Manejar el caso donde no existen preferencias para el usuario
    if pref is None:
        # Crear preferencias por defecto si no existen
        from app.notifications import schemas
        default_prefs = schemas.NotificationPreferencesUpdate(
            channels_inapp=True,
            channels_email=False
        )
        pref = crud.upsert_preferences(db, notif.user_id, default_prefs)
    
    # Ahora pref no puede ser None
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


# --- Weigh-in helpers ---


logger = logging.getLogger(__name__)


def get_user_timezone(db: Session, user_id: int | str) -> str:
    pref = crud.get_preferences(db, user_id)
    return pref.tz if pref and pref.tz else DEFAULT_TZ


def parse_local_time(t: str) -> tuple[int, int]:
    hour, minute = map(int, t.split(":"))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("invalid time")
    return hour, minute


def upcoming_weekly_occurrences(
    start_dt_local: datetime,
    target_weekday: int,
    hour: int,
    minute: int,
    weeks: int,
) -> list[datetime]:
    tz = start_dt_local.tzinfo
    first_date = start_dt_local.date()
    days_ahead = (target_weekday - start_dt_local.weekday()) % 7
    first_date = first_date + timedelta(days=days_ahead)
    first_dt = datetime.combine(first_date, time(hour, minute), tzinfo=tz)
    if first_dt < start_dt_local:
        first_dt = first_dt + timedelta(days=7)
    occurrences = []
    current = first_dt
    for _ in range(weeks):
        occurrences.append(current)
        current = current + timedelta(days=7)
    return occurrences


def make_dedupe_key(user_id: int | str, local_date: date) -> str:
    return f"weigh_in:{user_id}:{local_date.isoformat()}"


def ensure_notifications(
    db: Session,
    user_id: int | str,
    tz: str,
    occurrences_local: list[datetime],
) -> tuple[int, datetime | None]:
    created = 0
    first_local: datetime | None = None
    pref = crud.get_preferences(db, user_id)
    for dt_local in occurrences_local:
        if pref and pref.quiet_hours_start_local and pref.quiet_hours_end_local:
            start = datetime.combine(
                dt_local.date(), pref.quiet_hours_start_local, tzinfo=ZoneInfo(tz)
            )
            end = datetime.combine(
                dt_local.date(), pref.quiet_hours_end_local, tzinfo=ZoneInfo(tz)
            )
            if pref.quiet_hours_start_local < pref.quiet_hours_end_local:
                in_quiet = start <= dt_local < end
            else:
                in_quiet = dt_local >= start or dt_local < end
            if in_quiet:
                new_dt = dt_local + timedelta(hours=1)
                if new_dt.date() == dt_local.date():
                    dt_local = new_dt
                else:
                    logger.info(
                        "weigh_in within quiet hours", extra={"user_id": user_id}
                    )

        dedupe_key = make_dedupe_key(user_id, dt_local.date())
        existing = db.execute(
            select(models.Notification).where(
                models.Notification.user_id == user_id,
                models.Notification.dedupe_key == dedupe_key,
                models.Notification.type == models.NotificationType.WEIGH_IN,
                models.Notification.status == models.NotificationStatus.SCHEDULED,
            )
        ).scalar_one_or_none()
        if existing:
            continue
        scheduled_at = dt_local.astimezone(ZoneInfo("UTC"))
        notif = schemas.NotificationCreate(
            user_id=int(user_id),
            category=models.NotificationCategory.PROGRESS,
            type=models.NotificationType.WEIGH_IN,
            title="Weigh-in Reminder",
            body="Time to weigh yourself",
            payload={
                "local_iso": dt_local.replace(second=0, microsecond=0).isoformat(),
                "tz": tz,
            },
            scheduled_at_utc=scheduled_at,
            dedupe_key=dedupe_key,
        )
        crud.create_notification(db, notif)
        created += 1
        if not first_local:
            first_local = dt_local
    return created, first_local


# ---------------------------------------------------------------------------
# Auto daily reminders (on-demand)
# ---------------------------------------------------------------------------


def ensure_auto_daily_reminders(db: Session, user_id: int) -> int:
    """Create simple, deduplicated reminders for today's key actions.

    - If no meals logged today: remind to register meals
    - If no weight entry today: remind to register weight

    Uses the user's preferred timezone (or default) to compute "today".
    Returns the number of notifications created.
    """
    pref = crud.get_preferences(db, user_id)
    tz = pref.tz if pref and pref.tz else DEFAULT_TZ
    now_local = datetime.now(ZoneInfo(tz))
    today_local = now_local.date()

    created = 0

    # Meals check
    try:
        from app.nutrition import models as nut_models
    except Exception:  # pragma: no cover - defensive import
        nut_models = None
    if nut_models is not None:
        has_meals = (
            db.query(nut_models.NutritionMeal)
            .filter(
                nut_models.NutritionMeal.user_id == user_id,
                nut_models.NutritionMeal.date == today_local,
            )
            .first()
            is not None
        )
        if not has_meals:
            dedupe_key = f"auto:meals:{user_id}:{today_local.isoformat()}"
            notif = schemas.NotificationCreate(
                user_id=user_id,
                category=models.NotificationCategory.NUTRITION,
                type=models.NotificationType.MEAL_REMINDER,
                title="Registra tus comidas",
                body="Aún no has registrado comidas hoy.",
                payload={"date": today_local.isoformat(), "tz": tz},
                scheduled_at_utc=now_local.astimezone(ZoneInfo("UTC")),
                dedupe_key=dedupe_key,
            )
            row = crud.create_notification(db, notif)
            # Mark delivered in-app for visibility
            dispatch_notification(db, row.id)
            created += 1

    # Weight check
    try:
        from app.progress import models as prog_models
    except Exception:  # pragma: no cover - defensive import
        prog_models = None
    if prog_models is not None:
        weight_exists = (
            db.query(prog_models.ProgressEntry)
            .filter(
                prog_models.ProgressEntry.user_id == user_id,
                prog_models.ProgressEntry.date == today_local,
                prog_models.ProgressEntry.metric == prog_models.MetricEnum.weight,
            )
            .first()
            is not None
        )
        if not weight_exists:
            dedupe_key = f"auto:weight:{user_id}:{today_local.isoformat()}"
            notif = schemas.NotificationCreate(
                user_id=user_id,
                category=models.NotificationCategory.PROGRESS,
                type=models.NotificationType.PROGRESS_DAILY,
                title="Registra tu peso",
                body="Aún no has registrado tu peso hoy.",
                payload={"date": today_local.isoformat(), "tz": tz},
                scheduled_at_utc=now_local.astimezone(ZoneInfo("UTC")),
                dedupe_key=dedupe_key,
            )
            row = crud.create_notification(db, notif)
            dispatch_notification(db, row.id)
            created += 1

    return created
