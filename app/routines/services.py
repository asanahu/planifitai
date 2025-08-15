from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from . import models, schemas
from app.auth.deps import UserContext
from fastapi import HTTPException, status
from app.notifications.tasks import schedule_routine
from app.progress import models as progress_models


def get_routine(db: Session, routine_id: int, user: UserContext):
    routine = (
        db.query(models.Routine)
        .options(
            selectinload(models.Routine.days).selectinload(models.RoutineDay.exercises)
        )
        .filter(models.Routine.id == routine_id, models.Routine.deleted_at == None)
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
        .filter(models.Routine.owner_id == user_id, models.Routine.deleted_at == None)
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
            models.Routine.is_template == True,
            models.Routine.is_public == True,
            models.Routine.deleted_at == None,
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
            models.Routine.deleted_at == None,
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
    db_routine = get_routine(db, routine_id, user)

    if db_routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    update_data = routine_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_routine, key, value)

    db.add(db_routine)
    db.commit()
    db.refresh(db_routine)
    return db_routine


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
        .filter(models.Routine.id == template_id, models.Routine.is_template == True)
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
            models.RoutineExercise.id == exercise_id, models.Routine.deleted_at == None
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
