from __future__ import annotations

import logging
from datetime import datetime
from datetime import time as dt_time
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db
from app.core.errors import ok
from app.schemas.notifications import (
    WeighInScheduleRequest,
    WeighInScheduleResponse,
)

from . import crud, models, schemas, services, tasks

logger = logging.getLogger(__name__)

# ensure models imported

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", response_model=schemas.NotificationPreferences)
def get_preferences(
    current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)
):
    pref = crud.get_preferences(db, current_user.id)
    if not pref:
        pref = crud.upsert_preferences(
            db, current_user.id, schemas.NotificationPreferencesUpdate()
        )
    return pref


@router.put("/preferences", response_model=schemas.NotificationPreferences)
def put_preferences(
    prefs: schemas.NotificationPreferencesUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.upsert_preferences(db, current_user.id, prefs)


class RoutineScheduleRequest(BaseModel):
    routine_id: int
    active_days: Dict[str, bool] | None = None
    hour_local: Optional[str] = None


@router.post(
    "/schedule/routines",
    deprecated=True,
    summary="(DEPRECATED) Programar notificaciones de rutina",
    description=(
        "Este endpoint será retirado. Usa "
        "`POST /api/v1/routines/{id}/schedule-notifications` en su lugar."
    ),
    responses={
        200: {
            "description": "Notificaciones programadas",
            "content": {
                "application/json": {
                    "example": {"ok": True, "data": {"scheduled_count": 3}}
                }
            },
        }
    },
)
def schedule_routines(
    data: RoutineScheduleRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hour_str = data.hour_local or "07:30"
    hour, minute = map(int, hour_str.split(":"))
    res = services.schedule_routine_notifications(
        db,
        user_id=current_user.id,
        routine_id=data.routine_id,
        active_days=data.active_days or {},
        hour_local=dt_time(hour, minute),
    )
    headers = {
        "Deprecation": "true",
        "Link": f'</api/v1/routines/{data.routine_id}/schedule-notifications>; rel="successor-version"',
    }
    logger.info(
        "schedule_routine_notifications",
        extra={
            "event": "schedule_routine_notifications",
            "routine_id": data.routine_id,
            "user_id": current_user.id,
            "scheduled_count": res["scheduled_count"],
            "deprecated_call": True,
        },
    )
    return ok(res, headers=headers)


class NutritionScheduleRequest(BaseModel):
    meal_times_local: Optional[Dict[str, str]] = None
    water_every_min: Optional[int] = None


@router.post("/schedule/nutrition")
def schedule_nutrition(
    data: NutritionScheduleRequest,
    current_user: UserContext = Depends(get_current_user),
):
    tasks.schedule_nutrition_reminders_task.delay(
        user_id=current_user.id,
        meal_times=data.meal_times_local,
        water_every_min=data.water_every_min,
    )
    return {"scheduled": True}


@router.post(
    "/schedule/weigh-in",
    response_model=WeighInScheduleResponse,
    summary="Schedule weekly weigh-in notifications",
    description=(
        "Create weekly weigh-in reminders for the authenticated user. "
        "`day_of_week` uses 0=Monday .. 6=Sunday. `local_time` is interpreted in"
        " the user's timezone (default `Europe/Madrid`)."
        " `weeks_ahead` defines how many upcoming reminders are created."
    ),
    responses={
        200: {
            "description": "Notifications scheduled",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": {
                            "scheduled_count": 8,
                            "first_scheduled_local": "2024-08-19T09:00:00+02:00",
                            "timezone": "Europe/Madrid",
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "error": {
                            "code": "COMMON_VALIDATION",
                            "message": "day_of_week must be between 0 and 6",
                        },
                    }
                }
            },
        },
    },
)
def schedule_weigh_in_endpoint(
    req: WeighInScheduleRequest,
    current_user: UserContext = Depends(get_current_user),
):
    result = tasks.schedule_weigh_in_notifications_task.delay(
        current_user.id,
        req.day_of_week,
        req.local_time,
        req.weeks_ahead,
    )
    data = result.get() if hasattr(result, "get") else result
    return ok(WeighInScheduleResponse(**data))


@router.get("/", response_model=list[schemas.NotificationOut])
def list_notifications_endpoint(
    status: Optional[str] = Query(None),
    limit: int = 50,
    offset: int = 0,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifs = crud.list_notifications(
        db, current_user.id, status=status, limit=limit, offset=offset
    )
    return notifs


@router.patch("/{notif_id}/read", response_model=schemas.NotificationOut)
def mark_read_endpoint(
    notif_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = crud.get_notification(db, current_user.id, notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return crud.mark_read(db, notif)


@router.patch("/{notif_id}/dismiss", response_model=schemas.NotificationOut)
def mark_dismiss_endpoint(
    notif_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = crud.get_notification(db, current_user.id, notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return crud.mark_dismissed(db, notif)


@router.post("/test/send", response_model=schemas.NotificationOut)
def test_send(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = crud.create_notification(
        db,
        schemas.NotificationCreate(
            user_id=current_user.id,
            category=models.NotificationCategory.SYSTEM,
            type=models.NotificationType.CUSTOM,
            title="Test",
            body="This is a test",
            scheduled_at_utc=datetime.utcnow(),
        ),
    )
    services.dispatch_notification(db, notif.id)
    return notif
