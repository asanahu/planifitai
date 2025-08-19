import logging
import time
from datetime import date
from datetime import time as dt_time
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db
from app.core.errors import (
    ok,
)
from app.dependencies import get_owned_routine
from app.notifications import services as notif_services
from app.progress import schemas as progress_schemas
from app.schemas import adherence as adherence_schemas
from app.schemas.exercises import ExerciseCatalogResponse, ExerciseRead
from app.services import adherence as adherence_services
from app.utils.datetimes import week_bounds

from . import models, schemas, services

router = APIRouter(prefix="/routines", tags=["routines"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.RoutineRead)
def create_routine(
    routine: schemas.RoutineCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(services.create_routine(db=db, routine=routine, user=current_user))


@router.get("/", response_model=List[schemas.RoutineRead])
def read_routines(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.get_routines_by_user(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
    )


@router.get("/templates", response_model=List[schemas.RoutineRead])
def read_public_templates(
    skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    return ok(services.get_public_templates(db=db, skip=skip, limit=limit))


@router.get(
    "/exercise-catalog",
    response_model=ExerciseCatalogResponse,
    summary="Catálogo de ejercicios",
    description="Listado filtrable/paginable de ejercicios. Semana/MVP helper para frontend.",
)
def get_exercise_catalog(
    q: str | None = Query(None),
    muscle: str | None = Query(None),
    equipment: str | None = Query(None),
    level: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = services.list_exercises(
        db,
        q=q,
        muscle=muscle,
        equipment=equipment,
        level=level,
        limit=limit,
        offset=offset,
    )
    items = [ExerciseRead.model_validate(r) for r in rows]
    return ok(
        ExerciseCatalogResponse(items=items, total=total, limit=limit, offset=offset)
    )


@router.get(
    "/{routine_id}",
    response_model=schemas.RoutineRead,
    summary="Retrieve routine details with adherence",
    description=(
        "Returns a routine and its adherence for the requested week. "
        "`week` may be `this`, `last` or `custom` (default `this`).\n"
        "When using `week=custom`, both `start` and `end` must be provided in"
        " `YYYY-MM-DD` format. Weeks are Monday–Sunday in the `Europe/Madrid`"
        " timezone."
    ),
    responses={
        200: {
            "description": "Routine with adherence data",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": {
                            "id": 123,
                            "name": "Summer Shred",
                            "adherence": {
                                "routine_id": 123,
                                "week_start": "2024-08-05",
                                "week_end": "2024-08-11",
                                "planned": 3,
                                "completed": 2,
                                "adherence_pct": 67,
                                "status": "fair",
                            },
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
                            "message": "start and end required for custom week",
                        },
                    }
                }
            },
        },
    },
)
def read_routine(
    routine: models.Routine = Depends(get_owned_routine),
    week: Literal["this", "last", "custom"] = "this",
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    tz = "Europe/Madrid"
    start_date: date
    end_date: date
    if week == "this":
        start_date, end_date = week_bounds("this_week", tz)
    elif week == "last":
        start_date, end_date = week_bounds("last_week", tz)
    elif week == "custom":
        if start is None or end is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start and end required for custom week",
            )
        if start > end:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start must be before or equal to end",
            )
        start_date, end_date = start, end
    else:
        start_date = end_date = date.today()  # pragma: no cover

    start_ts = time.time()
    if week == "custom":
        adherence = adherence_services.compute_weekly_workout_adherence(
            db=db, routine_id=routine.id, start=start_date, range="custom", tz=tz
        )
    else:
        range_map = {"this": "this_week", "last": "last_week"}
        adherence = adherence_services.compute_weekly_workout_adherence(
            db=db, routine_id=routine.id, range=range_map[week], tz=tz
        )
    duration_ms = int((time.time() - start_ts) * 1000)
    logger.info(
        "routine_read",
        extra={
            "routine_id": routine.id,
            "week": week,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "planned": adherence.planned,
            "completed": adherence.completed,
            "percentage": adherence.adherence_pct,
            "duration_ms": duration_ms,
        },
    )

    routine_data = schemas.RoutineRead.model_validate(routine)
    routine_data.adherence = adherence
    return ok(routine_data)


@router.get(
    "/{routine_id}/adherence", response_model=adherence_schemas.AdherenceResponse
)
def get_routine_adherence(
    routine: models.Routine = Depends(get_owned_routine),
    range: Literal["last_week", "this_week", "custom"] = "last_week",
    tz: str = "Europe/Madrid",
    start: date | None = None,
    db: Session = Depends(get_db),
):
    return ok(
        adherence_services.compute_weekly_workout_adherence(
            db=db, routine_id=routine.id, start=start, range=range, tz=tz
        )
    )


@router.put("/{routine_id}", response_model=schemas.RoutineRead)
def update_routine(
    routine_id: int,
    routine_update: schemas.RoutineUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    routine = services.update_routine_guarded(
        db=db,
        routine_id=routine_id,
        user_id=current_user.id,
        payload=routine_update,
    )
    return ok(schemas.RoutineRead.model_validate(routine))


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    services.delete_routine(db=db, routine_id=routine.id, user=current_user)
    return ok(None, status.HTTP_204_NO_CONTENT)


@router.post("/clone", response_model=schemas.RoutineRead)
def clone_template(
    clone_request: schemas.CloneFromTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.clone_template(
            db=db, template_id=clone_request.template_id, user=current_user
        )
    )


@router.post("/{routine_id}/days", response_model=schemas.RoutineDayRead)
def create_routine_day(
    day: schemas.RoutineDayCreate,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.add_day_to_routine(
            db=db, routine_id=routine.id, day=day, user=current_user
        )
    )


@router.put("/{routine_id}/days/{day_id}", response_model=schemas.RoutineDayRead)
def update_routine_day(
    day_id: int,
    day_update: schemas.RoutineDayUpdate,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.update_routine_day(
            db=db, day_id=day_id, day_update=day_update, user=current_user
        )
    )


@router.delete("/{routine_id}/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine_day(
    day_id: int,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    services.delete_routine_day(db=db, day_id=day_id, user=current_user)
    return ok(None, status.HTTP_204_NO_CONTENT)


@router.post(
    "/{routine_id}/days/{day_id}/exercises", response_model=schemas.RoutineExerciseRead
)
def create_routine_exercise(
    day_id: int,
    exercise: schemas.RoutineExerciseCreate,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.add_exercise_to_day(
            db=db, day_id=day_id, exercise=exercise, user=current_user
        )
    )


@router.put(
    "/{routine_id}/days/{day_id}/exercises/{exercise_id}",
    response_model=schemas.RoutineExerciseRead,
)
def update_routine_exercise(
    exercise_id: int,
    exercise_update: schemas.RoutineExerciseUpdate,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.update_routine_exercise(
            db=db,
            exercise_id=exercise_id,
            exercise_update=exercise_update,
            user=current_user,
        )
    )


@router.delete(
    "/{routine_id}/days/{day_id}/exercises/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_routine_exercise(
    exercise_id: int,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    services.delete_routine_exercise(db=db, exercise_id=exercise_id, user=current_user)
    return ok(None, status.HTTP_204_NO_CONTENT)


@router.post(
    "/{routine_id}/schedule-notifications",
    summary="Programar notificaciones de rutina (canónico)",
    description="Crea recordatorios para los próximos 7 días en la zona horaria del usuario.",
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
def schedule_notifications(
    payload: schemas.ScheduleNotificationsRequest | None = None,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    if not routine.active_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Routine has no active days",
        )
    hour = payload.hour if payload else None
    hour_local = dt_time(hour, 0) if hour is not None else dt_time(7, 30)
    res = notif_services.schedule_routine_notifications(
        db,
        user_id=current_user.id,
        routine_id=routine.id,
        active_days=routine.active_days,
        hour_local=hour_local,
    )
    logger.info(
        "schedule_routine_notifications",
        extra={
            "event": "schedule_routine_notifications",
            "routine_id": routine.id,
            "user_id": current_user.id,
            "scheduled_count": res["scheduled_count"],
            "deprecated_call": False,
        },
    )
    return ok(res)


@router.post(
    "/{routine_id}/days/{day_id}/exercises/{exercise_id}/complete",
    response_model=progress_schemas.ProgressEntryRead,
)
def complete_exercise(
    exercise_id: int,
    payload: schemas.CompleteExerciseRequest,
    routine: models.Routine = Depends(get_owned_routine),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return ok(
        services.complete_exercise(
            db=db, exercise_id=exercise_id, user=current_user, payload=payload
        )
    )
