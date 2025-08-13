import logging
from app.core.celery_utils import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="notifications.schedule_routine")
def schedule_routine(user_id: int, routine_id: int, active_days: dict, hour: int | None = None):
    """Stub task that logs scheduling of a routine."""
    logger.info(
        "Scheduling routine %s for user %s on %s at hour %s", routine_id, user_id, active_days, hour
    )
    return True

@celery_app.task(name="notifications.schedule_nutrition")
def schedule_nutrition(user_id: int, times: dict | None = None):
    """Stub task that logs scheduling of nutrition reminders."""
    logger.info("Scheduling nutrition reminders for user %s: %s", user_id, times)
    return True
