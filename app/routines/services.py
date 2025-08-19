import logging
from datetime import datetime
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UserContext
from app.notifications.tasks import schedule_routine
from app.progress import models as progress_models

from . import models, schemas

logger = logging.getLogger(__name__)


def list_exercises(
    db: Session,
    q: str | None = None,
    muscle: str | None = None,
    equipment: str | None = None,
    level: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[object], int]:
    """Return exercise catalog rows and total count with optional filters."""

    Exercise = getattr(models, "Exercise", None) or getattr(models, "ExerciseCatalog")

    stmt = select(Exercise)
    where_clauses = []

    if q:
        pattern = f"%{q.lower()}%"
        search_cols = [func.lower(Exercise.name)]
        if hasattr(Exercise, "pattern"):
            search_cols.append(func.lower(getattr(Exercise, "pattern")))
        if hasattr(Exercise, "tags"):
            search_cols.append(func.lower(getattr(Exercise, "tags")))
        where_clauses.append(or_(*[c.like(pattern) for c in search_cols]))

    if muscle:
        muscle_col = None
        for attr in ["muscle_groups", "muscles", "muscle", "category"]:
            if hasattr(Exercise, attr):
                muscle_col = getattr(Exercise, attr)
                break
        if muscle_col is not None:
            coltype = muscle_col.type.__class__.__name__.lower()
            if "array" in coltype or "json" in coltype:
                where_clauses.append(muscle_col.contains([muscle]))
            else:
                where_clauses.append(func.lower(muscle_col).like(f"%{muscle.lower()}%"))

    if equipment and hasattr(Exercise, "equipment"):
        where_clauses.append(
            func.lower(getattr(Exercise, "equipment")) == equipment.lower()
        )

    if level:
        level_col = None
        for attr in ["level", "difficulty", "description"]:
            if hasattr(Exercise, attr):
                level_col = getattr(Exercise, attr)
                break
        if level_col is not None:
            where_clauses.append(func.lower(level_col) == level.lower())

    if where_clauses:
        stmt = stmt.where(and_(*where_clauses))

    count_stmt = select(func.count()).select_from(Exercise)
    if where_clauses:
        count_stmt = count_stmt.where(and_(*where_clauses))
    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(func.lower(Exercise.name)).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()
    return rows, total


def get_routine(db: Session, routine_id: int, user: UserContext):
    routine = (
        db.query(models.Routine)
        .options(
            selectinload(models.Routine.days).selectinload(models.RoutineDay.exercises)
        )
        .filter(models.Routine.id == routine_id, models.Routine.deleted_at.is_(None))
        .first()
    )
    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found"
        )
    if not routine.is_public and routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return routine


def get_routines_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Routine)
        .options(
            selectinload(models.Routine.days).selectinload(models.RoutineDay.exercises)
        )
        .filter(models.Routine.owner_id == user_id, models.Routine.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_public_templates(db: Session, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Routine)
        .options(
            selectinload(models.Routine.days).selectinload(models.RoutineDay.exercises)
        )
        .filter(
            models.Routine.is_template,
            models.Routine.is_public,
            models.Routine.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_routine(db: Session, routine: schemas.RoutineCreate, user: UserContext):
    # Check for unique name for the same user
    existing_routine = (
        db.query(models.Routine)
        .filter(
            models.Routine.owner_id == user.id,
            models.Routine.name == routine.name,
            models.Routine.deleted_at.is_(None),
        )
        .first()
    )
    if existing_routine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A routine with this name already exists.",
        )

    db_routine = models.Routine(
        name=routine.name,
        description=routine.description,
        is_template=routine.is_template,
        is_public=routine.is_public,
        active_days=routine.active_days,
        start_date=routine.start_date,
        end_date=routine.end_date,
        owner_id=user.id,
    )
    db.add(db_routine)
    db.commit()
    db.refresh(db_routine)
    for day_data in routine.days:
        db_day = models.RoutineDay(
            routine_id=db_routine.id,
            weekday=day_data.weekday,
            order_index=day_data.order_index,
        )
        db.add(db_day)
        db.commit()
        db.refresh(db_day)

        for exercise_data in day_data.exercises:
            db_exercise = models.RoutineExercise(
                routine_day_id=db_day.id, **exercise_data.dict()
            )
            db.add(db_exercise)
            db.commit()
            db.refresh(db_exercise)

    db.refresh(db_routine)  # Refresh to get all nested relationships
    if routine.active_days:
        schedule_routine.delay(user.id, db_routine.id, routine.active_days, None)
    return db_routine


def update_routine(
    db: Session,
    routine_id: int,
    routine_update: schemas.RoutineUpdate,
    user: UserContext,
):
    return update_routine_guarded(
        db=db, routine_id=routine_id, user_id=user.id, payload=routine_update
    )


def update_routine_guarded(
    db: Session,
    routine_id: int,
    user_id: int,
    payload: schemas.RoutineUpdate | dict,
) -> models.Routine:
    """Apply soft-delete and pause guards before updating a routine."""
    routine = (
        db.query(models.Routine)
        .filter(models.Routine.id == routine_id, models.Routine.owner_id == user_id)
        .first()
    )
    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found"
        )

    soft_deleted = False
    if hasattr(routine, "deleted_at"):
        soft_deleted = routine.deleted_at is not None
    elif hasattr(routine, "is_deleted"):
        soft_deleted = bool(routine.is_deleted)
    if soft_deleted:
        logger.info(
            "routine_update_guard",
            extra={
                "routine_id": routine_id,
                "user_id": user_id,
                "soft_deleted": True,
                "paused": False,
                "updated_fields": [],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found"
        )

    paused = False
    if hasattr(routine, "active"):
        paused = routine.active is False
    elif hasattr(routine, "status"):
        paused = routine.status == "paused"
    if paused:
        logger.info(
            "routine_update_guard",
            extra={
                "routine_id": routine_id,
                "user_id": user_id,
                "soft_deleted": False,
                "paused": True,
                "updated_fields": [],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Routine is paused; cannot update",
        )

    data = (
        payload.model_dump(exclude_unset=True)
        if hasattr(payload, "model_dump")
        else dict(payload)
    )
    protected = {"id", "owner_id", "created_at", "updated_at", "deleted_at"}
    update_data = {
        k: v for k, v in data.items() if hasattr(routine, k) and k not in protected
    }
    for key, value in update_data.items():
        setattr(routine, key, value)

    db.add(routine)
    db.commit()
    db.refresh(routine)

    logger.info(
        "routine_updated",
        extra={
            "routine_id": routine_id,
            "user_id": user_id,
            "paused": paused,
            "soft_deleted": soft_deleted,
            "updated_fields": list(update_data.keys()),
        },
    )
    return routine


def delete_routine(db: Session, routine_id: int, user: UserContext):
    db_routine = get_routine(db, routine_id, user)

    if db_routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    db_routine.deleted_at = datetime.utcnow()
    db.add(db_routine)
    db.commit()
    return {"detail": "Routine soft deleted"}


def clone_template(db: Session, template_id: int, user: UserContext):
    template = (
        db.query(models.Routine)
        .options(
            selectinload(models.Routine.days).selectinload(models.RoutineDay.exercises)
        )
        .filter(models.Routine.id == template_id, models.Routine.is_template)
        .first()
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Create a new routine from the template
    new_routine = models.Routine(
        name=f"{template.name} (Copy)",
        description=template.description,
        is_template=False,
        is_public=False,
        active_days=template.active_days,
        owner_id=user.id,
    )
    db.add(new_routine)
    db.commit()
    db.refresh(new_routine)

    # Copy days and exercises
    for day in template.days:
        new_day = models.RoutineDay(
            routine_id=new_routine.id,
            weekday=day.weekday,
            order_index=day.order_index,
        )
        db.add(new_day)
        db.commit()
        db.refresh(new_day)

        for exercise in day.exercises:
            new_exercise = models.RoutineExercise(
                routine_day_id=new_day.id,
                exercise_name=exercise.exercise_name,
                sets=exercise.sets,
                reps=exercise.reps,
                time_seconds=exercise.time_seconds,
                tempo=exercise.tempo,
                rest_seconds=exercise.rest_seconds,
                notes=exercise.notes,
                order_index=exercise.order_index,
            )
            db.add(new_exercise)
            db.commit()
            db.refresh(new_exercise)

    db.refresh(new_routine)
    return new_routine


def add_day_to_routine(
    db: Session, routine_id: int, day: schemas.RoutineDayCreate, user: UserContext
):
    db_routine = get_routine(db, routine_id, user)
    if db_routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    db_day = models.RoutineDay(routine_id=routine_id, **day.dict())
    db.add(db_day)
    db.commit()
    db.refresh(db_day)
    return db_day


def update_routine_day(
    db: Session, day_id: int, day_update: schemas.RoutineDayUpdate, user: UserContext
):
    db_day = db.query(models.RoutineDay).filter(models.RoutineDay.id == day_id).first()
    if not db_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine day not found"
        )

    get_routine(db, db_day.routine_id, user)  # Check for ownership

    update_data = day_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_day, key, value)

    db.add(db_day)
    db.commit()
    db.refresh(db_day)
    return db_day


def delete_routine_day(db: Session, day_id: int, user: UserContext):
    db_day = db.query(models.RoutineDay).filter(models.RoutineDay.id == day_id).first()
    if not db_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine day not found"
        )

    get_routine(db, db_day.routine_id, user)  # Check for ownership

    db.delete(db_day)
    db.commit()
    return {"detail": "Routine day deleted"}


def add_exercise_to_day(
    db: Session, day_id: int, exercise: schemas.RoutineExerciseCreate, user: UserContext
):
    db_day = db.query(models.RoutineDay).filter(models.RoutineDay.id == day_id).first()
    if not db_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine day not found"
        )

    get_routine(db, db_day.routine_id, user)  # Check for ownership

    db_exercise = models.RoutineExercise(routine_day_id=day_id, **exercise.dict())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


def update_routine_exercise(
    db: Session,
    exercise_id: int,
    exercise_update: schemas.RoutineExerciseUpdate,
    user: UserContext,
):
    db_exercise = (
        db.query(models.RoutineExercise)
        .filter(models.RoutineExercise.id == exercise_id)
        .first()
    )
    if not db_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )

    get_routine(db, db_exercise.day.routine_id, user)  # Check for ownership

    update_data = exercise_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_exercise, key, value)

    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


def delete_routine_exercise(db: Session, exercise_id: int, user: UserContext):
    db_exercise = (
        db.query(models.RoutineExercise)
        .filter(models.RoutineExercise.id == exercise_id)
        .first()
    )
    if not db_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )

    get_routine(db, db_exercise.day.routine_id, user)  # Check for ownership

    db.delete(db_exercise)
    db.commit()
    return {"detail": "Exercise deleted"}


def schedule_routine_notifications(
    db: Session, routine_id: int, user: UserContext, hour: int | None = None
):
    routine = get_routine(db, routine_id, user)
    if routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    if not routine.active_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Routine has no active days"
        )
    schedule_routine.delay(user.id, routine.id, routine.active_days, hour)
    return {"detail": "notifications scheduled"}


def complete_exercise(
    db: Session,
    exercise_id: int,
    user: UserContext,
    payload: schemas.CompleteExerciseRequest,
):
    db_exercise = (
        db.query(models.RoutineExercise)
        .join(models.RoutineDay)
        .join(models.Routine)
        .filter(
            models.RoutineExercise.id == exercise_id,
            models.Routine.deleted_at.is_(None),
        )
        .first()
    )
    if not db_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )
    routine = db_exercise.day.routine
    if routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    date_val = payload.timestamp.date()
    existing = (
        db.query(progress_models.ProgressEntry)
        .filter(
            progress_models.ProgressEntry.user_id == user.id,
            progress_models.ProgressEntry.date == date_val,
            progress_models.ProgressEntry.metric == progress_models.MetricEnum.workout,
        )
        .first()
    )
    if existing:
        return existing
    entry = progress_models.ProgressEntry(
        user_id=user.id,
        date=date_val,
        metric=progress_models.MetricEnum.workout,
        value=payload.duration_seconds or 1,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
