import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.progress import models as progress_models
from app.user_profile.models import ActivityLevel, Goal, UserProfile
from services import food_search
from services.units import compute_factor

from . import crud, models, schemas

logger = logging.getLogger(__name__)


ACTIVITY_FACTORS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}

GOAL_DELTAS = {
    Goal.LOSE_WEIGHT: -0.2,
    Goal.MAINTAIN_WEIGHT: 0.0,
    Goal.GAIN_WEIGHT: 0.15,
}


def compute_auto_targets(
    profile: UserProfile, params: schemas.TargetsAutoParams | None = None
) -> dict:
    if not all(
        [
            profile.age,
            profile.height_cm,
            profile.weight_kg,
            profile.activity_level,
            profile.goal,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile incomplete for target calculation",
        )
    params = params or schemas.TargetsAutoParams()
    weight = profile.weight_kg
    height = profile.height_cm
    age = profile.age
    # neutral BMR since sex not stored
    bmr = 10 * weight + 6.25 * height - 5 * age - 78
    act_factor = ACTIVITY_FACTORS.get(profile.activity_level, 1.2)
    goal_delta = GOAL_DELTAS.get(profile.goal, 0.0)
    calories = int(round(bmr * act_factor * (1 + goal_delta)))
    protein_g = Decimal(str(weight * params.protein_per_kg)).quantize(Decimal("0.01"))
    fat_g = Decimal(str(calories * params.fat_ratio / 9)).quantize(Decimal("0.01"))
    carbs_kcal = calories - (int(protein_g * 4) + int(fat_g * 9))
    carbs_g = Decimal(str(carbs_kcal / 4)).quantize(Decimal("0.01"))
    method = {
        "formula": "mifflin-st-jeor",
        "activity_factor": act_factor,
        "goal_delta": goal_delta,
        "neutral": True,
        "protein_per_kg": params.protein_per_kg,
        "fat_ratio": params.fat_ratio,
    }
    return {
        "calories_target": calories,
        "protein_g_target": protein_g,
        "carbs_g_target": carbs_g,
        "fat_g_target": fat_g,
        "method": method,
    }


def get_or_create_target(
    db: Session, user_id: int, day: date
) -> models.NutritionTarget:
    target = crud.get_target(db, user_id, day)
    if target:
        return target
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile required for targets",
        )
    data = compute_auto_targets(profile)
    target = crud.upsert_target(db, user_id, day, data, models.TargetSource.auto)
    return target


def day_meal_totals(meals: List[models.NutritionMeal]) -> schemas.MacroTotals:
    totals = schemas.MacroTotals()
    for meal in meals:
        for item in meal.items:
            totals.calories_kcal += item.calories_kcal
            totals.protein_g += item.protein_g
            totals.carbs_g += item.carbs_g
            totals.fat_g += item.fat_g
    return totals


def get_day_log(db: Session, user_id: int, day: date) -> schemas.DayLogRead:
    meals = (
        db.query(models.NutritionMeal)
        .options(selectinload(models.NutritionMeal.items))
        .filter(
            models.NutritionMeal.user_id == user_id, models.NutritionMeal.date == day
        )
        .order_by(models.NutritionMeal.id)
        .all()
    )
    water_logs = crud.list_water_logs(db, user_id, day)
    water_total = sum(w.volume_ml for w in water_logs)
    target = get_or_create_target(db, user_id, day)
    totals = day_meal_totals(meals)
    adherence = {
        "calories": (
            float(totals.calories_kcal) / target.calories_target
            if target.calories_target
            else None
        ),
        "protein": (
            float(totals.protein_g) / float(target.protein_g_target)
            if target.protein_g_target
            else None
        ),
        "carbs": (
            float(totals.carbs_g) / float(target.carbs_g_target)
            if target.carbs_g_target
            else None
        ),
        "fat": (
            float(totals.fat_g) / float(target.fat_g_target)
            if target.fat_g_target
            else None
        ),
    }
    return schemas.DayLogRead(
        date=day,
        meals=[schemas.MealRead.model_validate(m) for m in meals],
        totals=totals,
        water_total_ml=water_total,
        targets=schemas.TargetsRead.model_validate(target),
        adherence=adherence,
    )


def get_summary(
    db: Session, user_id: int, start: date, end: date
) -> schemas.SummaryRead:
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date range"
        )
    current = start
    total_totals = schemas.MacroTotals()
    adherence_acc = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    days = 0
    while current <= end:
        day_log = get_day_log(db, user_id, current)
        total_totals.calories_kcal += day_log.totals.calories_kcal
        total_totals.protein_g += day_log.totals.protein_g
        total_totals.carbs_g += day_log.totals.carbs_g
        total_totals.fat_g += day_log.totals.fat_g
        for k in adherence_acc:
            adherence_acc[k] += day_log.adherence.get(k, 0) if day_log.adherence else 0
        days += 1
        current += timedelta(days=1)
    avg = schemas.MacroTotals(
        calories_kcal=total_totals.calories_kcal / days if days else 0,
        protein_g=total_totals.protein_g / days if days else 0,
        carbs_g=total_totals.carbs_g / days if days else 0,
        fat_g=total_totals.fat_g / days if days else 0,
    )
    adherence = {k: (v / days if days else 0) for k, v in adherence_acc.items()}
    return schemas.SummaryRead(
        start=start,
        end=end,
        days=days,
        totals=total_totals,
        average=avg,
        adherence=adherence,
    )


def schedule_reminders(db: Session, user_id: int, times: Dict):
    from app.notifications.tasks import schedule_nutrition

    schedule_nutrition.delay(user_id, times)
    return {"scheduled": True}


def post_daily_summary(db: Session, user_id: int, day: date):
    day_log = get_day_log(db, user_id, day)
    created: list[str] = []
    updated: list[str] = []

    def upsert(metric: progress_models.MetricEnum, value: float, unit: str):
        existing = (
            db.query(progress_models.ProgressEntry)
            .filter(
                progress_models.ProgressEntry.user_id == user_id,
                progress_models.ProgressEntry.date == day,
                progress_models.ProgressEntry.metric == metric,
            )
            .first()
        )
        if existing:
            existing.value = value
            existing.unit = unit
            updated.append(metric.value)
        else:
            entry = progress_models.ProgressEntry(
                user_id=user_id, date=day, metric=metric, value=value, unit=unit
            )
            db.add(entry)
            created.append(metric.value)

    upsert(
        progress_models.MetricEnum.calories_intake,
        float(day_log.totals.calories_kcal),
        "kcal",
    )
    upsert(progress_models.MetricEnum.protein_g, float(day_log.totals.protein_g), "g")
    upsert(progress_models.MetricEnum.carbs_g, float(day_log.totals.carbs_g), "g")
    upsert(progress_models.MetricEnum.fat_g, float(day_log.totals.fat_g), "g")
    upsert(progress_models.MetricEnum.water_ml, float(day_log.water_total_ml), "ml")
    db.commit()
    return {"created": created, "updated": updated}


# --- MealItem flexible creation ---


def _extract_unit_weight_grams(portion_suggestions: Dict | None) -> Decimal | None:
    if not portion_suggestions:
        return None
    # Common keys that might represent grams per unit
    for key in [
        "unit_g",
        "unit_grams",
        "grams_per_unit",
        "g_per_unit",
        "per_unit_g",
    ]:
        val = portion_suggestions.get(key)
        if isinstance(val, (int, float, str)):
            try:
                d = Decimal(str(val))
                if d > 0:
                    return d
            except Exception:
                continue
    return None


def create_meal_item_flexible(
    db: Session, user_id: int, meal_id: int, payload: schemas.MealItemAddFlexible
):
    """Create a meal item supporting either legacy-manual or food-driven inputs.

    Returns a tuple (read_schema, orm_item) where read_schema may include meta fields
    like factor_used and portion_estimated.
    """
    logger = logging.getLogger(__name__)

    # Legacy manual path (fully specified item fields)
    legacy_complete = (
        payload.serving_qty is not None
        and payload.serving_unit is not None
        and payload.calories_kcal is not None
        and payload.protein_g is not None
        and payload.carbs_g is not None
        and payload.fat_g is not None
    )
    if legacy_complete:
        item = crud.add_meal_item(
            db,
            user_id,
            meal_id,
            schemas.MealItemCreate(
                food_id=payload.food_id,  # type: ignore[arg-type]
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
            ),
        )
        read = schemas.MealItemRead.model_validate(item)
        return read, item

    # Flexible food-driven path
    if not payload.quantity or not payload.unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="quantity and unit are required for food-driven items",
        )

    details: schemas.FoodDetails | None = None
    source_name = None
    if payload.food_id:
        details = food_search.get_food(db, payload.food_id)
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Food not found"
            )
        source_name = details.name
    else:
        # query required validated at schema level
        hits = food_search.search_foods(db, payload.query, page=1, page_size=1)
        if not hits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No foods found for query '{payload.query}'",
            )
        top = hits[0]
        details = food_search.get_food(db, top.id)
        if not details:
            # Extremely rare, means race; treat as not found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Food not found"
            )
        source_name = details.name

    unit_weight = _extract_unit_weight_grams(details.portion_suggestions)
    fr = compute_factor(payload.quantity, payload.unit, unit_weight_grams=unit_weight)

    def _d(x: float | Decimal | None) -> Decimal:
        try:
            return Decimal("0") if x is None else Decimal(str(x))
        except Exception:
            return Decimal("0")

    base_cal = _d(details.calories_kcal)
    base_pro = _d(details.protein_g)
    base_carb = _d(details.carbs_g)
    base_fat = _d(details.fat_g)

    calories = (base_cal * fr.factor).quantize(Decimal("0.01"))
    protein = (base_pro * fr.factor).quantize(Decimal("0.01"))
    carbs = (base_carb * fr.factor).quantize(Decimal("0.01"))
    fat = (base_fat * fr.factor).quantize(Decimal("0.01"))

    # Manual override precedence
    if payload.manual_override:
        mo = payload.manual_override
        if mo.calories_kcal is not None:
            calories = Decimal(str(mo.calories_kcal)).quantize(Decimal("0.01"))
        if mo.protein_g is not None:
            protein = Decimal(str(mo.protein_g)).quantize(Decimal("0.01"))
        if mo.carbs_g is not None:
            carbs = Decimal(str(mo.carbs_g)).quantize(Decimal("0.01"))
        if mo.fat_g is not None:
            fat = Decimal(str(mo.fat_g)).quantize(Decimal("0.01"))
        logger.info("MealItem manual override applied for meal_id=%s", meal_id)

    if fr.portion_estimated:
        logger.info(
            "Unit weight unknown; using estimated portion for meal_id=%s (query=%s food_id=%s)",
            meal_id,
            payload.query,
            payload.food_id,
        )

    # Persist as snapshot
    serving_unit = fr.serving_unit
    serving_qty = Decimal(str(payload.quantity)).quantize(Decimal("0.01"))
    item_payload = schemas.MealItemCreate(
        food_id=None,  # keep FK optional (Food uses string id)
        food_name=source_name,
        serving_qty=serving_qty,
        serving_unit=serving_unit,
        calories_kcal=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        fiber_g=payload.fiber_g,
        sugar_g=payload.sugar_g,
        sodium_mg=payload.sodium_mg,
        order_index=payload.order_index or 0,
    )
    item = crud.add_meal_item(db, user_id, meal_id, item_payload)
    read = schemas.MealItemRead.model_validate(item)
    read.factor_used = fr.factor.quantize(Decimal("0.0001"))
    read.portion_estimated = fr.portion_estimated
    return read, item
