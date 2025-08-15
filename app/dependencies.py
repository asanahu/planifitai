from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.auth.deps import UserContext, get_current_user
from app.nutrition.models import NutritionMeal
from app.progress.models import ProgressEntry
from app.routines.models import Routine, RoutineDay


def get_owned_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
) -> NutritionMeal:
    """
    Dependency that gets a meal by its ID and verifies it belongs to the current authenticated user.
    """
    meal = (
        db.query(NutritionMeal)
        .options(selectinload(NutritionMeal.items))
        .filter(NutritionMeal.id == meal_id, NutritionMeal.user_id == current_user.id)
        .first()
    )
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found",
        )
    return meal


def get_owned_progress_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
) -> ProgressEntry:
    """
    Dependency that gets a progress entry by its ID and verifies it belongs to the current authenticated user.
    """
    entry = (
        db.query(ProgressEntry)
        .filter(ProgressEntry.id == entry_id, ProgressEntry.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress entry not found",
        )
    return entry


def get_owned_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
) -> Routine:
    """
    Dependency that gets a routine by its ID and verifies it belongs to the current authenticated user.
    """
    routine = (
        db.query(Routine)
        .options(selectinload(Routine.days).selectinload(RoutineDay.exercises))
        .filter(
            Routine.id == routine_id,
            Routine.owner_id == current_user.id,
            Routine.deleted_at.is_(None),
        )
        .first()
    )
    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )
    return routine
