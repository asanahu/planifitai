import logging
from datetime import datetime, date, timedelta
from typing import List, Tuple, Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, cast, String
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import UserContext
from app.notifications.tasks import schedule_routine
from app.progress import models as progress_models

from . import models, schemas
from app.services.rules_engine import IMPACT_WORDS

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
        if hasattr(Exercise, "description"):
            search_cols.append(func.lower(getattr(Exercise, "description")))
        if hasattr(Exercise, "pattern"):
            search_cols.append(func.lower(getattr(Exercise, "pattern")))
        if hasattr(Exercise, "tags"):
            search_cols.append(func.lower(getattr(Exercise, "tags")))
        where_clauses.append(or_(*[c.like(pattern) for c in search_cols]))

    if muscle:
        def _norm(s: str) -> str:
            return (
                s.lower()
                .replace("á", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("ü", "u")
            )

        synonyms_map = {
            "pecho": ["pecho", "pectorales", "chest", "pectorals"],
            "espalda": ["espalda", "back", "lats", "dorsales"],
            "hombros": ["hombros", "shoulders", "delts", "deltoids"],
            "biceps": ["biceps", "bíceps", "bicep"],
            "triceps": ["triceps", "tríceps", "tricep"],
            "antebrazos": ["antebrazos", "forearms"],
            "abdominales": ["abdominales", "abs", "core", "oblicuos", "obliques"],
            "gluteos": ["gluteos", "glúteos", "glutes"],
            "cuadriceps": ["cuadriceps", "cuádriceps", "quads", "quadriceps", "quad"],
            "isquiotibiales": ["isquiotibiales", "hamstrings"],
            "gemelos": ["gemelos", "calves", "calf"],
        }
        mkey = _norm(muscle)
        values = synonyms_map.get(mkey, [muscle])

        muscle_col = None
        for attr in ["muscle_groups", "muscles", "muscle", "category"]:
            if hasattr(Exercise, attr):
                muscle_col = getattr(Exercise, attr)
                break
        if muscle_col is not None:
            coltype = muscle_col.type.__class__.__name__.lower()
            if "array" in coltype or "json" in coltype:
                conds = [func.lower(cast(muscle_col, String)).like(f"%{v.lower()}%") for v in values]
                where_clauses.append(or_(*conds))
            else:
                conds = [func.lower(muscle_col).like(f"%{v.lower()}%") for v in values]
                where_clauses.append(or_(*conds))

    if equipment and hasattr(Exercise, "equipment"):
        where_clauses.append(
            func.lower(getattr(Exercise, "equipment")) == equipment.lower()
        )

    if level:
        # Filtramos solo si existe una columna/atributo claro de nivel
        level_col = getattr(Exercise, "level", None)
        if level_col is not None:
            lvl = level.lower()
            # Normaliza sinónimos (EN/ES)
            base_map = {
                "advanced": "expert",
                "advance": "expert",
                "avanzado": "expert",
                "experto": "expert",
                "principiante": "beginner",
                "intermedio": "intermediate",
            }
            lvl = base_map.get(lvl, lvl)
            # Acepta variantes EN y ES en DB
            variants = {
                "expert": ["expert", "experto", "advanced", "avanzado"],
                "beginner": ["beginner", "principiante"],
                "intermediate": ["intermediate", "intermedio"],
            }.get(lvl, [lvl])
            where_clauses.append(func.lower(level_col).in_([v.lower() for v in variants]))

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


def get_exercise_filters(db: Session) -> dict:
    """Return distinct equipment and muscle groups from the catalog.

    Uses simple scanning to ensure cross-dialect compatibility.
    """
    Exercise = getattr(models, "ExerciseCatalog")
    equipments: set[str] = set()
    muscles: set[str] = set()
    rows = db.query(Exercise.equipment, Exercise.muscle_groups).limit(5000).all()
    # Canonical Spanish labels for common muscles/equipment
    def _norm(s: str) -> str:
        return (
            s.lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ü", "u")
        )
    muscle_canon = {
        "pecho": ["pecho", "pectorales", "chest", "pectorals"],
        "espalda": ["espalda", "back", "lats", "dorsales"],
        "hombros": ["hombros", "shoulders", "delts", "deltoids"],
        "bíceps": ["biceps", "bíceps", "bicep"],
        "tríceps": ["triceps", "tríceps", "tricep"],
        "antebrazos": ["antebrazos", "forearms"],
        "abdominales": ["abdominales", "abs", "core", "oblicuos", "obliques"],
        "glúteos": ["gluteos", "glúteos", "glutes"],
        "cuádriceps": ["cuadriceps", "cuádriceps", "quads", "quadriceps", "quad"],
        "isquiotibiales": ["isquiotibiales", "hamstrings"],
        "gemelos": ["gemelos", "calves", "calf"],
    }
    muscle_index = { _norm(v): k for k, arr in muscle_canon.items() for v in arr }
    equip_canon = {
        "peso corporal": ["bodyweight", "body weight", "peso corporal"],
        "mancuernas": ["dumbbell", "mancuernas"],
        "barra": ["barbell", "barra"],
        "kettlebell": ["kettlebell"],
        "máquina": ["machine", "máquina", "machine smith", "smith machine"],
        "polea": ["cable", "polea"],
        "banda elástica": ["band", "resistance band", "banda elástica"],
        "balón medicinal": ["medicine ball", "balón medicinal"],
    }
    equip_index = { _norm(v): k for k, arr in equip_canon.items() for v in arr }
    for eq, mg in rows:
        if eq:
            key = equip_index.get(_norm(str(eq)))
            equipments.add(key or str(eq))
        if mg:
            try:
                for m in mg:
                    if m:
                        key = muscle_index.get(_norm(str(m)))
                        muscles.add(key or str(m))
            except TypeError:
                # fallback if stored as string
                key = muscle_index.get(_norm(str(mg)))
                muscles.add(key or str(mg))
    return {
        "equipment": sorted(equipments),
        "muscles": sorted(muscles),
    }


def get_routines_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Routine)
        .options(
            selectinload(models.Routine.days).selectinload(models.RoutineDay.exercises)
        )
        .filter(models.Routine.owner_id == user_id, models.Routine.deleted_at.is_(None))
        .order_by(models.Routine.created_at.asc(), models.Routine.id.asc())
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
            equipment=getattr(day_data, "equipment", None),
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
    # Mark this specific exercise as completed for the given date
    from .models import RoutineExerciseCompletion  # local import to avoid cycles

    existing_ce = (
        db.query(RoutineExerciseCompletion)
        .filter(
            RoutineExerciseCompletion.user_id == user.id,
            RoutineExerciseCompletion.routine_exercise_id == exercise_id,
            RoutineExerciseCompletion.date == date_val,
        )
        .first()
    )
    if not existing_ce:
        ce = RoutineExerciseCompletion(
            user_id=user.id, routine_exercise_id=exercise_id, date=date_val
        )
        db.add(ce)
        db.commit()

    # If all exercises for the day are completed on this date, ensure day-level ProgressEntry exists
    day_exercises = [ex.id for ex in db_exercise.day.exercises]
    completed_for_day = (
        db.query(RoutineExerciseCompletion.routine_exercise_id)
        .filter(
            RoutineExerciseCompletion.user_id == user.id,
            RoutineExerciseCompletion.routine_exercise_id.in_(day_exercises),
            RoutineExerciseCompletion.date == date_val,
        )
        .distinct()
        .count()
    )
    if completed_for_day >= len(day_exercises) and len(day_exercises) > 0:
        existing = (
            db.query(progress_models.ProgressEntry)
            .filter(
                progress_models.ProgressEntry.user_id == user.id,
                progress_models.ProgressEntry.date == date_val,
                progress_models.ProgressEntry.metric
                == progress_models.MetricEnum.workout,
            )
            .first()
        )
        if not existing:
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
        return existing
    # If day is not fully completed, return a generic status
    return {"detail": "exercise_marked"}


def uncomplete_exercise(
    db: Session,
    exercise_id: int,
    user: UserContext,
    date_val: date,
):
    from .models import RoutineExerciseCompletion  # local import

    db_exercise = db.get(models.RoutineExercise, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    routine = db_exercise.day.routine
    if routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    ce = (
        db.query(RoutineExerciseCompletion)
        .filter(
            RoutineExerciseCompletion.user_id == user.id,
            RoutineExerciseCompletion.routine_exercise_id == exercise_id,
            RoutineExerciseCompletion.date == date_val,
        )
        .first()
    )
    if ce:
        db.delete(ce)
        db.commit()
    # If there is a day-level ProgressEntry for that date but not all exercises are completed anymore, remove it
    day_exercises = [ex.id for ex in db_exercise.day.exercises]
    remaining = (
        db.query(RoutineExerciseCompletion)
        .filter(
            RoutineExerciseCompletion.user_id == user.id,
            RoutineExerciseCompletion.routine_exercise_id.in_(day_exercises),
            RoutineExerciseCompletion.date == date_val,
        )
        .count()
    )
    if remaining < len(day_exercises):
        pe = (
            db.query(progress_models.ProgressEntry)
            .filter(
                progress_models.ProgressEntry.user_id == user.id,
                progress_models.ProgressEntry.date == date_val,
                progress_models.ProgressEntry.metric
                == progress_models.MetricEnum.workout,
            )
            .first()
        )
        if pe:
            db.delete(pe)
            db.commit()
    return {"detail": "exercise_unmarked"}


def complete_day(
    db: Session,
    routine_id: int,
    day_id: int,
    user: UserContext,
    date_override: date | None = None,
):
    """Mark a routine day as completed by creating a workout ProgressEntry for today.

    Idempotent: if an entry for today already exists, return it.
    Guards ownership by ensuring the day belongs to the user's routine.
    """
    # Ensure the day belongs to the routine and the routine belongs to the user
    db_day = (
        db.query(models.RoutineDay)
        .join(models.Routine)
        .filter(
            models.RoutineDay.id == day_id,
            models.RoutineDay.routine_id == routine_id,
            models.Routine.deleted_at.is_(None),
        )
        .first()
    )
    if not db_day:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Day not found")
    routine = db_day.routine
    if routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    today = date_override or date.today()
    existing = (
        db.query(progress_models.ProgressEntry)
        .filter(
            progress_models.ProgressEntry.user_id == user.id,
            progress_models.ProgressEntry.date == today,
            progress_models.ProgressEntry.metric == progress_models.MetricEnum.workout,
        )
        .first()
    )
    if existing:
        return existing
    entry = progress_models.ProgressEntry(
        user_id=user.id,
        date=today,
        metric=progress_models.MetricEnum.workout,
        value=1,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def uncomplete_day(
    db: Session,
    routine_id: int,
    day_id: int,
    user: UserContext,
    date_override: date | None = None,
):
    """Undo completion for a routine day by removing the workout progress entry for that date.

    No-op if there is no entry.
    """
    db_day = (
        db.query(models.RoutineDay)
        .join(models.Routine)
        .filter(
            models.RoutineDay.id == day_id,
            models.RoutineDay.routine_id == routine_id,
            models.Routine.deleted_at.is_(None),
        )
        .first()
    )
    if not db_day:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Day not found")
    routine = db_day.routine
    if routine.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    target_date = date_override or date.today()
    entry = (
        db.query(progress_models.ProgressEntry)
        .filter(
            progress_models.ProgressEntry.user_id == user.id,
            progress_models.ProgressEntry.date == target_date,
            progress_models.ProgressEntry.metric == progress_models.MetricEnum.workout,
        )
        .first()
    )
    if entry:
        db.delete(entry)
        db.commit()
    return {"detail": "uncompleted"}


def _progress_value(sets: int | None, reps: int | None, seconds: int | None) -> tuple[int | None, int | None, int | None]:
    """Small progression heuristic used to build next week's plan.

    - If sets present: +1 up to 5
    - Else if reps present: +1 up to 20
    - Else if seconds present: +5 up to 120
    """
    if sets is not None:
        sets = min(5, max(1, sets + 1))
    elif reps is not None:
        reps = min(20, max(1, reps + 1))
    elif seconds is not None:
        seconds = min(120, max(5, seconds + 5))
    return sets, reps, seconds


def create_next_week_from_routine(db: Session, routine_id: int, user: UserContext) -> models.Routine:
    """Create a new routine representing the following week by applying a
    simple progression heuristic to the current routine's exercises.

    Keeps weekdays/order and copies optional equipment per day.
    """
    routine = get_routine(db, routine_id, user)

    # Build RoutineCreate payload
    next_name = f"{routine.name} — Semana siguiente"
    payload = schemas.RoutineCreate(
        name=next_name,
        description=routine.description,
        is_template=False,
        is_public=False,
        active_days=routine.active_days,
        start_date=None,
        end_date=None,
        days=[],
    )

    # Compute start_date for next week: if current routine has start_date, add 7 days; otherwise next Monday
    base_start: date
    if getattr(routine, "start_date", None):
        try:
            base_start = routine.start_date.date()  # type: ignore[union-attr]
        except Exception:
            base_start = date.today()
    else:
        base_start = date.today()
    # normalize to Monday of base week
    monday_offset = (base_start.weekday() + 0) % 7  # weekday(): Mon=0..Sun=6
    monday = base_start - timedelta(days=monday_offset)
    next_monday = monday + timedelta(days=7)
    payload.start_date = datetime.combine(next_monday, datetime.min.time())

    for d in sorted(routine.days, key=lambda x: x.order_index):
        day_create = schemas.RoutineDayCreate(
            weekday=d.weekday,
            order_index=d.order_index,
            equipment=getattr(d, "equipment", None),
            exercises=[],
        )
        ex_sorted = sorted(d.exercises, key=lambda x: x.order_index)
        for idx, ex in enumerate(ex_sorted):
            alt = _pick_alternative_exercise(
                db=db,
                base_ex=ex,
                allowed_equipment=set(getattr(d, "equipment", []) or []),
                order_index=idx,
            )
            new_name = alt.name if alt else ex.exercise_name
            new_id = getattr(alt, "id", None) if alt else ex.exercise_id
            new_sets, new_reps, new_secs = _progress_value(ex.sets, ex.reps, ex.time_seconds)
            day_create.exercises.append(
                schemas.RoutineExerciseCreate(
                    exercise_id=new_id,
                    exercise_name=new_name,
                    sets=new_sets or 1,
                    reps=new_reps,
                    time_seconds=new_secs,
                    tempo=ex.tempo,
                    rest_seconds=ex.rest_seconds,
                    notes=ex.notes,
                    order_index=ex.order_index,
                )
            )
        payload.days.append(day_create)

    # Create and return
    try:
        return create_routine(db=db, routine=payload, user=user)
    except HTTPException as exc:  # handle unique name clash by suffixing a counter
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            alt = schemas.RoutineCreate(**{**payload.model_dump(), "name": f"{routine.name} — Semana siguiente (1)"})
            return create_routine(db=db, routine=alt, user=user)
        raise


# --------- Variety helpers ---------
def _norm(s: str) -> str:
    return (
        s.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
    )


def _avoid_impact(name: str) -> bool:
    return all(w not in _norm(name) for w in IMPACT_WORDS)


def _like_any(text: str, subs: Iterable[str]) -> bool:
    t = _norm(text)
    return any(sub in t for sub in subs)


def _keyword_alternatives(name: str) -> list[str]:
    """Fallback alternatives by keyword family if catalog is insufficient."""
    families: dict[str, list[str]] = {
        "push": ["flexiones inclinadas", "flexiones diamante", "flexiones declinadas", "press banca con mancuernas"],
        "press": ["press hombro mancuernas", "push press con mancuernas", "arnold press"],
        "squat": ["sentadilla goblet", "sentadilla búlgara", "zancadas", "sentadilla frontal"],
        "lunge": ["zancadas inversas", "zancadas caminando", "split squat"],
        "row": ["remo con mancuerna", "remo en barra", "remo con banda"],
        "pull": ["dominadas supinas", "jalón al pecho con banda", "remo con banda"],
        "deadlift": ["peso muerto rumano", "peso muerto con mancuerna", "hip hinge con banda"],
        "hip": ["puente de glúteo", "hip thrust con mancuerna", "hip thrust a una pierna"],
        "core": ["plancha", "dead bug", "bird dog"],
        "curl": ["curl martillo", "curl concentrado", "curl con banda"],
        "triceps": ["extensión tríceps con mancuerna", "fondos en banco", "jalón tríceps con banda"],
    }
    t = _norm(name)
    for k, alts in families.items():
        if k in t:
            return alts
    return []


def _pick_alternative_exercise(
    db: Session,
    base_ex: models.RoutineExercise,
    allowed_equipment: set[str],
    order_index: int = 0,
) -> Optional[models.ExerciseCatalog]:
    """Suggest an alternative exercise using the catalog when possible.

    - Avoid exact same name
    - Respect allowed equipment (if provided)
    - Avoid high impact exercises
    - Prefer same muscle groups/category if known
    - Deterministic selection based on order_index
    """
    Exercise = getattr(models, "ExerciseCatalog")
    base_row: Optional[models.ExerciseCatalog] = None
    if base_ex.exercise_id:
        base_row = db.get(Exercise, base_ex.exercise_id)
    if not base_row:
        # try name match
        q = (
            db.query(Exercise)
            .filter(func.lower(Exercise.name) == _norm(base_ex.exercise_name))
            .first()
        )
        base_row = q if q else None

    # gather candidates
    cands: list[models.ExerciseCatalog] = (
        db.query(Exercise).limit(1000).all()
    )

    def _allowed_eq(eq: Optional[str]) -> bool:
        if not allowed_equipment:
            return True
        if not eq:
            return True
        # Map common aliases EN/ES
        alias = {
            "bodyweight": {"bodyweight", "peso corporal"},
            "dumbbells": {"dumbbells", "mancuernas"},
            "barbell": {"barbell", "barra"},
            "kettlebell": {"kettlebell"},
            "bands": {"bands", "band", "banda", "bandas", "resistance band"},
            "machine": {"machine", "máquina", "maquina", "smith machine", "machine smith"},
            "cable": {"cable", "polea"},
        }
        allowed_norm = set()
        for k in allowed_equipment:
            k_norm = _norm(k)
            for base, vals in alias.items():
                if k_norm in {_norm(v) for v in vals} or k_norm == base:
                    allowed_norm.update({_norm(v) for v in vals})
                    allowed_norm.add(base)
        if not allowed_norm:
            allowed_norm = {_norm(x) for x in allowed_equipment}
        return _norm(eq) in allowed_norm

    # primary filters
    filtered = [
        r for r in cands
        if _norm(r.name) != _norm(base_ex.exercise_name)
        and _avoid_impact(r.name)
        and _allowed_eq(getattr(r, "equipment", None))
    ]

    def _overlap(a: Iterable[str] | None, b: Iterable[str] | None) -> bool:
        if not a or not b:
            return False
        sa = { _norm(x) for x in a if x }
        sb = { _norm(x) for x in b if x }
        return len(sa & sb) > 0

    with_overlap: list[models.ExerciseCatalog] = []
    same_category: list[models.ExerciseCatalog] = []
    if base_row:
        for r in filtered:
            if _overlap(getattr(r, "muscle_groups", None), getattr(base_row, "muscle_groups", None)):
                with_overlap.append(r)
            elif getattr(r, "category", None) and getattr(base_row, "category", None) and _norm(r.category) == _norm(base_row.category):
                same_category.append(r)

    # choose bucket
    bucket = with_overlap or same_category or filtered
    if bucket:
        bucket_sorted = sorted(bucket, key=lambda x: _norm(x.name))
        idx = order_index % len(bucket_sorted)
        return bucket_sorted[idx]

    # fallback keyword-based alternatives
    for alt_name in _keyword_alternatives(base_ex.exercise_name):
        if _avoid_impact(alt_name):
            # Try resolve to catalog entry by name
            row = (
                db.query(Exercise)
                .filter(func.lower(Exercise.name) == _norm(alt_name))
                .first()
            )
            if row and _allowed_eq(getattr(row, "equipment", None)):
                return row

    return None
