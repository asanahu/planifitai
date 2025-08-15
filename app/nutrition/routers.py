from datetime import date
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.deps import UserContext, get_current_user
from app.user_profile.models import UserProfile
from app.dependencies import get_owned_meal

from . import schemas, services, crud, models

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post(
    "/meal", response_model=schemas.MealRead, status_code=status.HTTP_201_CREATED
)
def create_meal(
    payload: schemas.MealCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    if payload.date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Future date not allowed"
        )
    meal = crud.create_meal(db, current_user.id, payload)
    return schemas.MealRead.model_validate(meal)


@router.get("/", response_model=schemas.DayLogRead)
def get_day(
    date: date,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    day_log = services.get_day_log(db, current_user.id, date)
    return day_log


@router.patch("/meal/{meal_id}", response_model=schemas.MealRead)
def update_meal(
    payload: schemas.MealUpdate,
    meal: models.NutritionMeal = Depends(get_owned_meal),
    db: Session = Depends(get_db),
):
    meal = crud.update_meal(db, meal.user_id, meal.id, payload)
    return schemas.MealRead.model_validate(meal)


@router.delete("/meal/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal: models.NutritionMeal = Depends(get_owned_meal), db: Session = Depends(get_db)
):
    crud.delete_meal(db, meal.user_id, meal.id)
    return


@router.post(
    "/meal/{meal_id}/items",
    response_model=schemas.MealItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
    payload: schemas.MealItemCreate,
    meal: models.NutritionMeal = Depends(get_owned_meal),
    db: Session = Depends(get_db),
):
    item = crud.add_meal_item(db, meal.user_id, meal.id, payload)
    return schemas.MealItemRead.model_validate(item)


@router.patch("/meal/{meal_id}/items/{item_id}", response_model=schemas.MealItemRead)
def update_item(
    item_id: int,
    payload: schemas.MealItemUpdate,
    meal: models.NutritionMeal = Depends(get_owned_meal),
    db: Session = Depends(get_db),
):
    item = crud.update_meal_item(db, meal.user_id, meal.id, item_id, payload)
    return schemas.MealItemRead.model_validate(item)


@router.delete(
    "/meal/{meal_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_item(
    item_id: int,
    meal: models.NutritionMeal = Depends(get_owned_meal),
    db: Session = Depends(get_db),
):
    crud.delete_meal_item(db, meal.user_id, meal.id, item_id)
    return


@router.post(
    "/water", response_model=schemas.WaterLogRead, status_code=status.HTTP_201_CREATED
)
def create_water_log(
    payload: schemas.WaterLogCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    log = crud.create_water_log(db, current_user.id, payload)
    return schemas.WaterLogRead.model_validate(log)


@router.get("/water")
def get_water_logs(
    date: date,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    logs = crud.list_water_logs(db, current_user.id, date)
    total = sum(l.volume_ml for l in logs)
    return {
        "total_ml": total,
        "logs": [schemas.WaterLogRead.model_validate(l) for l in logs],
    }


@router.get("/targets", response_model=schemas.TargetsRead)
def get_targets(
    date: date,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    target = services.get_or_create_target(db, current_user.id, date)
    return schemas.TargetsRead.model_validate(target)


@router.post("/targets/custom", response_model=schemas.TargetsRead)
def set_custom_targets(
    payload: schemas.TargetsSetCustom,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    data = payload.model_dump(exclude={"date"})
    target = crud.upsert_target(
        db, current_user.id, payload.date, data, models.TargetSource.custom
    )
    return schemas.TargetsRead.model_validate(target)


@router.post("/targets/auto/recompute", response_model=schemas.TargetsRead)
def recompute_targets(
    date: date,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    profile = db.query(UserProfile).filter_by(user_id=current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile required for targets",
        )
    data = services.compute_auto_targets(profile)
    target = crud.upsert_target(
        db, current_user.id, date, data, models.TargetSource.auto
    )
    return schemas.TargetsRead.model_validate(target)


@router.get("/summary", response_model=schemas.SummaryRead)
def summary(
    start: date,
    end: date,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return services.get_summary(db, current_user.id, start, end)


@router.post("/schedule-reminders")
def schedule_reminders(
    times: Dict | None = None,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return services.schedule_reminders(db, current_user.id, times or {})


@router.post("/post-daily-summary")
def post_daily_summary(
    date: date,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return services.post_daily_summary(db, current_user.id, date)
