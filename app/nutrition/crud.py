from datetime import date, datetime
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from . import models, schemas


# Meal operations


def create_meal(
    db: Session, user_id: int, payload: schemas.MealCreate
) -> models.NutritionMeal:
    meal = models.NutritionMeal(
        user_id=user_id,
        date=payload.date,
        meal_type=payload.meal_type,
        name=payload.name,
        notes=payload.notes,
    )
    for idx, item in enumerate(payload.items):
        meal.items.append(
            models.NutritionMealItem(
                food_id=item.food_id,
                food_name=item.food_name,
                serving_qty=item.serving_qty,
                serving_unit=item.serving_unit,
                calories_kcal=item.calories_kcal,
                protein_g=item.protein_g,
                carbs_g=item.carbs_g,
                fat_g=item.fat_g,
                fiber_g=item.fiber_g,
                sugar_g=item.sugar_g,
                sodium_mg=item.sodium_mg,
                order_index=item.order_index if item.order_index is not None else idx,
            )
        )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def get_meal(db: Session, user_id: int, meal_id: int) -> models.NutritionMeal:
    meal = (
        db.query(models.NutritionMeal)
        .filter(models.NutritionMeal.id == meal_id)
        .first()
    )
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found"
        )
    if meal.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return meal


def update_meal(
    db: Session, user_id: int, meal_id: int, payload: schemas.MealUpdate
) -> models.NutritionMeal:
    meal = get_meal(db, user_id, meal_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(meal, field, value)
    db.commit()
    db.refresh(meal)
    return meal


def delete_meal(db: Session, user_id: int, meal_id: int) -> None:
    meal = get_meal(db, user_id, meal_id)
    db.delete(meal)
    db.commit()


def add_meal_item(
    db: Session, user_id: int, meal_id: int, payload: schemas.MealItemCreate
) -> models.NutritionMealItem:
    meal = get_meal(db, user_id, meal_id)
    item = models.NutritionMealItem(
        meal_id=meal.id,
        food_id=payload.food_id,
        food_name=payload.food_name,
        serving_qty=payload.serving_qty,
        serving_unit=payload.serving_unit,
        calories_kcal=payload.calories_kcal,
        protein_g=payload.protein_g,
        carbs_g=payload.carbs_g,
        fat_g=payload.fat_g,
        fiber_g=payload.fiber_g,
        sugar_g=payload.sugar_g,
        sodium_mg=payload.sodium_mg,
        order_index=payload.order_index or 0,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_meal_item(
    db: Session,
    user_id: int,
    meal_id: int,
    item_id: int,
    payload: schemas.MealItemUpdate,
) -> models.NutritionMealItem:
    meal = get_meal(db, user_id, meal_id)
    item = (
        db.query(models.NutritionMealItem)
        .filter(
            models.NutritionMealItem.id == item_id,
            models.NutritionMealItem.meal_id == meal.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_meal_item(db: Session, user_id: int, meal_id: int, item_id: int) -> None:
    meal = get_meal(db, user_id, meal_id)
    item = (
        db.query(models.NutritionMealItem)
        .filter(
            models.NutritionMealItem.id == item_id,
            models.NutritionMealItem.meal_id == meal.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    db.delete(item)
    db.commit()


# Water logs


def create_water_log(
    db: Session, user_id: int, payload: schemas.WaterLogCreate
) -> models.NutritionWaterLog:
    log = models.NutritionWaterLog(user_id=user_id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_water_logs(
    db: Session, user_id: int, day: date
) -> List[models.NutritionWaterLog]:
    return (
        db.query(models.NutritionWaterLog)
        .filter(
            models.NutritionWaterLog.user_id == user_id,
            models.NutritionWaterLog.datetime_utc
            >= datetime.combine(day, datetime.min.time()),
            models.NutritionWaterLog.datetime_utc
            < datetime.combine(day, datetime.max.time()),
        )
        .order_by(models.NutritionWaterLog.datetime_utc)
        .all()
    )


# Targets


def get_target(db: Session, user_id: int, day: date) -> models.NutritionTarget | None:
    return (
        db.query(models.NutritionTarget)
        .filter(
            models.NutritionTarget.user_id == user_id,
            models.NutritionTarget.date == day,
        )
        .first()
    )


def upsert_target(
    db: Session,
    user_id: int,
    day: date,
    data: dict,
    source: models.TargetSource,
) -> models.NutritionTarget:
    target = get_target(db, user_id, day)
    if target:
        if (
            target.source == models.TargetSource.custom
            and source == models.TargetSource.auto
        ):
            return target
        for field, value in data.items():
            setattr(target, field, value)
        target.source = source
    else:
        target = models.NutritionTarget(
            user_id=user_id, date=day, source=source, **data
        )
        db.add(target)
    db.commit()
    db.refresh(target)
    return target
