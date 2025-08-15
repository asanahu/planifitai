from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.deps import UserContext, get_current_user

from . import models, schemas, crud, services, tasks

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
    active_days: Dict[str, bool]
    hour_local: Optional[str] = "07:30"


@router.post("/schedule/routines")
def schedule_routines(
    data: RoutineScheduleRequest,
    current_user: UserContext = Depends(get_current_user),
):
    tasks.schedule_routine_notifications_task.delay(
        user_id=current_user.id,
        routine_id=data.routine_id,
        active_days=data.active_days,
        hour_local=data.hour_local or "07:30",
    )
    return {"scheduled": True}


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
