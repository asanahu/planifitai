from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Dict
from zoneinfo import ZoneInfo

from app.core.celery_utils import celery_app
from app.core.database import SessionLocal

from . import services

logger = logging.getLogger(__name__)


def _run_in_session(fn, *args, **kwargs):
    db = SessionLocal()
    try:
        return fn(db, *args, **kwargs)
    finally:
        db.close()


@celery_app.task(name="notifications.schedule_routine_notifications")
def schedule_routine_notifications_task(
    user_id: int, routine_id: int, active_days: Dict[str, bool], hour_local: str
) -> int:
    hour, minute = map(int, hour_local.split(":"))
    res = _run_in_session(
        services.schedule_routine_notifications,
        user_id=user_id,
        routine_id=routine_id,
        active_days=active_days,
        hour_local=time(hour, minute),
    )
    logger.info("scheduled %s routine notifications", len(res))
    return len(res)


@celery_app.task(name="notifications.schedule_nutrition_reminders")
def schedule_nutrition_reminders_task(
    user_id: int,
    meal_times: Dict[str, str] | None = None,
    water_every_min: int | None = None,
) -> int:
    res = _run_in_session(
        services.schedule_nutrition_reminders,
        user_id=user_id,
        meal_times_local=meal_times,
        water_every_min=water_every_min,
    )
    logger.info("scheduled %s nutrition notifications", len(res))
    return len(res)


@celery_app.task(name="notifications.schedule_weigh_in")
def schedule_weigh_in_notifications_task(
    user_id: int | str,
    day_of_week: int,
    local_time: str,
    weeks_ahead: int,
) -> dict:
    db = SessionLocal()
    try:
        tz = services.get_user_timezone(db, user_id)
        hour, minute = services.parse_local_time(local_time)
        now_local = datetime.now(ZoneInfo(tz))
        occ_local = services.upcoming_weekly_occurrences(
            now_local, day_of_week, hour, minute, weeks_ahead
        )
        created_count, first_local = services.ensure_notifications(
            db, user_id, tz, occ_local
        )
    finally:
        db.close()
    logger.info(
        "schedule_weigh_in",
        extra={
            "event": "schedule_weigh_in",
            "user_id": user_id,
            "tz": tz,
            "created": created_count,
            "first_local": first_local.isoformat() if first_local else None,
        },
    )
    return {
        "scheduled_count": created_count,
        "first_scheduled_local": (
            first_local.replace(second=0, microsecond=0).isoformat()
            if first_local
            else None
        ),
        "timezone": tz,
    }


# Backwards compatible task names used by other modules
@celery_app.task(name="notifications.schedule_routine")
def schedule_routine(
    user_id: int,
    routine_id: int,
    active_days: Dict[str, bool],
    hour_local: str | None = None,
) -> int:
    return schedule_routine_notifications_task(
        user_id, routine_id, active_days, hour_local or "07:30"
    )


@celery_app.task(name="notifications.schedule_nutrition")
def schedule_nutrition(
    user_id: int,
    times: Dict[str, str] | None = None,
    water_every_min: int | None = None,
) -> int:
    return schedule_nutrition_reminders_task(user_id, times, water_every_min)


@celery_app.task(name="notifications.dispatch_notification")
def dispatch_notification_task(notification_id: int) -> bool:
    res = _run_in_session(services.dispatch_notification, notification_id)
    logger.info("dispatched %s", notification_id)
    return bool(res)
