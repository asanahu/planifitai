"""Business logic for the AI endpoints."""
from __future__ import annotations

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import UserContext

from . import schemas
from . import embeddings as emb
from app.ai_client import get_ai_client


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def generate_workout_plan(
    user: UserContext, req: schemas.WorkoutPlanRequest, *, simulate: bool = False
) -> schemas.WorkoutPlan:
    """Return a very small deterministic workout plan."""
    client = get_ai_client()
    client.chat(user.id, [], simulate=simulate)

    day = schemas.WorkoutPlanDay(
        weekday="monday",
        focus="full body",
        exercises=[
            schemas.WorkoutExercise(name="push up", sets=3, reps=10, rest_sec=60),
        ],
    )
    plan = schemas.WorkoutPlan(
        name="Plan",
        days_per_week=req.days_per_week,
        days=[day],
        constraints={},
        total_time_min=45,
    )
    return plan


def generate_nutrition_plan(
    user: UserContext, req: schemas.NutritionPlanRequest, *, simulate: bool = False
) -> schemas.NutritionPlan:
    client = get_ai_client()
    client.chat(user.id, [], simulate=simulate)

    item = schemas.MealItem(
        name="manzana",
        qty=1,
        unit="unit",
        kcal=95,
        protein_g=0.3,
        carbs_g=25,
        fat_g=0.2,
    )
    meal = schemas.Meal(type="breakfast", items=[item], meal_kcal=95)
    day = schemas.NutritionDayPlan(
        date="2024-01-01",
        meals=[meal],
        totals={"kcal": 95, "protein_g": 0.3, "carbs_g": 25, "fat_g": 0.2},
    )
    plan = schemas.NutritionPlan(days=[day], targets={"kcal": 2000, "protein_g": 150, "carbs_g": 250, "fat_g": 70})
    return plan


# ---------------------------------------------------------------------------
# Chat & insights
# ---------------------------------------------------------------------------

def chat(user: UserContext, req: schemas.ChatRequest) -> schemas.ChatResponse:
    client = get_ai_client()
    resp = client.chat(user.id, [m.model_dump() for m in req.messages], simulate=req.simulate or False)
    return schemas.ChatResponse(reply=resp["reply"], actions=[])


def insights(user: UserContext, req: schemas.InsightsRequest) -> schemas.InsightsResponse:
    client = get_ai_client()
    client.chat(user.id, [], simulate=True)
    trends = {
        "weight": {"slope": 0.1, "weekly_change": 0.2, "plateau": False},
        "training_adherence": {"slope": 0.0, "weekly_change": 0.0, "plateau": False},
    }
    predictions = {"goal_eta_date": req.date_to}
    return schemas.InsightsResponse(trends=trends, predictions=predictions, suggestions=["keep going"])


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def recommend(user: UserContext, req: schemas.RecommendRequest, db: Session) -> schemas.RecommendResponse:
    base = db.query(emb.ContentEmbedding).filter_by(namespace=req.namespace, ref_id=req.ref_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="reference embedding not found")
    results = emb.search_similar(db, req.namespace, base.embedding, req.k)
    items = [schemas.RecommendItem(**r) for r in results if r["ref_id"] != req.ref_id]
    return schemas.RecommendResponse(items=items)

