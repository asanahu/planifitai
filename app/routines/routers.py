from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import services, schemas
from app.core.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/routines", tags=["routines"])

@router.post("/", response_model=schemas.RoutineRead)
def create_routine(
    routine: schemas.RoutineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.create_routine(db=db, routine=routine, user=current_user)


@router.get("/", response_model=List[schemas.RoutineRead])
def read_routines(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.get_routines_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/templates", response_model=List[schemas.RoutineRead])
def read_public_templates(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return services.get_public_templates(db=db, skip=skip, limit=limit)


@router.get("/{routine_id}", response_model=schemas.RoutineRead)
def read_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.get_routine(db=db, routine_id=routine_id, user=current_user)


@router.put("/{routine_id}", response_model=schemas.RoutineRead)
def update_routine(
    routine_id: int,
    routine_update: schemas.RoutineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.update_routine(
        db=db, routine_id=routine_id, routine_update=routine_update, user=current_user
    )


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    services.delete_routine(db=db, routine_id=routine_id, user=current_user)
    return


@router.post("/clone", response_model=schemas.RoutineRead)
def clone_template(
    clone_request: schemas.CloneFromTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.clone_template(
        db=db, template_id=clone_request.template_id, user=current_user
    )


@router.post("/{routine_id}/days", response_model=schemas.RoutineDayRead)
def create_routine_day(
    routine_id: int,
    day: schemas.RoutineDayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.add_day_to_routine(db=db, routine_id=routine_id, day=day, user=current_user)


@router.put("/{routine_id}/days/{day_id}", response_model=schemas.RoutineDayRead)
def update_routine_day(
    day_id: int,
    day_update: schemas.RoutineDayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.update_routine_day(db=db, day_id=day_id, day_update=day_update, user=current_user)


@router.delete("/{routine_id}/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine_day(
    day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    services.delete_routine_day(db=db, day_id=day_id, user=current_user)
    return


@router.post("/{routine_id}/days/{day_id}/exercises", response_model=schemas.RoutineExerciseRead)
def create_routine_exercise(
    day_id: int,
    exercise: schemas.RoutineExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.add_exercise_to_day(db=db, day_id=day_id, exercise=exercise, user=current_user)


@router.put("/{routine_id}/days/{day_id}/exercises/{exercise_id}", response_model=schemas.RoutineExerciseRead)
def update_routine_exercise(
    exercise_id: int,
    exercise_update: schemas.RoutineExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return services.update_routine_exercise(
        db=db, exercise_id=exercise_id, exercise_update=exercise_update, user=current_user
    )


@router.delete("/{routine_id}/days/{day_id}/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    services.delete_routine_exercise(db=db, exercise_id=exercise_id, user=current_user)
    return