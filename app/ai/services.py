"""Business logic for the AI endpoints."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai_client import get_ai_client
from app.auth.deps import UserContext

from . import embeddings as emb
from . import schemas

# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def _parse_json_payload(text: str) -> dict:
    """Extract a JSON object from a model reply.

    Tries direct json.loads, then fenced blocks, then curly braces heuristic.
    """
    try:
        return json.loads(text)
    except Exception:
        pass
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass
    # Heuristic: first { ... last }
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    raise HTTPException(status_code=502, detail="Invalid AI JSON response")


def generate_workout_plan(
    user: UserContext, req: schemas.WorkoutPlanRequest, *, simulate: bool = False
) -> schemas.WorkoutPlan:
    """Generate a workout plan via AI or return a deterministic stub when simulating."""
    from app.core.config import settings as _settings  # local import to avoid cycles
    if simulate or not _settings.OPENROUTER_KEY:
        day = schemas.WorkoutPlanDay(
            weekday="monday",
            focus="full body",
            exercises=[
                schemas.WorkoutExercise(name="push up", sets=3, reps=10, rest_sec=60),
            ],
        )
        return schemas.WorkoutPlan(
            name="Plan",
            days_per_week=req.days_per_week,
            days=[day],
            constraints={},
            total_time_min=45,
        )

    client = get_ai_client()
    sys_prompt = (
        "Eres PlanifitAI, un asistente de fitness. Devuelve únicamente JSON válido, sin explicaciones. "
        "Esquema: {name: str, days_per_week: int, days: [{weekday: str, focus?: str, exercises: [{name: str, sets: int, reps: int, rest_sec?: int, notes?: str}]}], constraints?: {str:str}, total_time_min?: int}."
    )
    user_prompt = (
        f"Genera un plan de entrenamiento personalizado en español. Días/semana: {req.days_per_week}. "
        f"Equipo disponible: {req.equipment or 'ninguno'}. Preferencias: {req.preferences or {}}. "
        "No devuelvas texto fuera del JSON."
    )
    resp = client.chat(
        user.id,
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    data = _parse_json_payload(resp.get("reply", ""))
    try:
        return schemas.WorkoutPlan.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI plan validation failed: {exc}")


def generate_nutrition_plan(
    user: UserContext, req: schemas.NutritionPlanRequest, *, simulate: bool = False
) -> schemas.NutritionPlan:
    from app.core.config import settings as _settings  # local import to avoid cycles
    if simulate or not _settings.OPENROUTER_KEY:
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
        return schemas.NutritionPlan(
            days=[day],
            targets={"kcal": 2000, "protein_g": 150, "carbs_g": 250, "fat_g": 70},
        )

    client = get_ai_client()
    today = date.today()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(max(1, req.days))]
    sys_prompt = (
        "Eres PlanifitAI, un nutricionista virtual. Devuelve únicamente JSON válido, sin explicaciones. "
        "Esquema: {days: [{date: str, meals: [{type: 'breakfast'|'lunch'|'dinner'|'snack', items: [{name:str, qty:number, unit:str, kcal:number, protein_g:number, carbs_g:number, fat_g:number}], meal_kcal:number}], totals:{kcal:number, protein_g:number, carbs_g:number, fat_g:number}}], targets:{kcal:number, protein_g:number, carbs_g:number, fat_g:number}}."
    )
    user_prompt = (
        f"Genera un plan de nutrición de {len(dates)} días en español para las fechas {dates}. "
        f"Preferencias/restricciones: {req.preferences or {}}. "
        "Usa unidades simples (g, ml, unidad). No devuelvas texto fuera del JSON."
    )
    resp = client.chat(
        user.id,
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    data = _parse_json_payload(resp.get("reply", ""))
    try:
        return schemas.NutritionPlan.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI nutrition validation failed: {exc}")


# ---------------------------------------------------------------------------
# Chat & insights
# ---------------------------------------------------------------------------


def chat(user: UserContext, req: schemas.ChatRequest) -> schemas.ChatResponse:
    client = get_ai_client()
    resp = client.chat(
        user.id, [m.model_dump() for m in req.messages], simulate=req.simulate or False
    )
    return schemas.ChatResponse(reply=resp["reply"], actions=[])


def insights(
    user: UserContext, req: schemas.InsightsRequest
) -> schemas.InsightsResponse:
    client = get_ai_client()
    client.chat(user.id, [], simulate=True)
    trends = {
        "weight": {"slope": 0.1, "weekly_change": 0.2, "plateau": False},
        "training_adherence": {"slope": 0.0, "weekly_change": 0.0, "plateau": False},
    }
    predictions = {"goal_eta_date": req.date_to}
    return schemas.InsightsResponse(
        trends=trends, predictions=predictions, suggestions=["keep going"]
    )


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def recommend(
    user: UserContext, req: schemas.RecommendRequest, db: Session
) -> schemas.RecommendResponse:
    base = (
        db.query(emb.ContentEmbedding)
        .filter_by(namespace=req.namespace, ref_id=req.ref_id)
        .first()
    )
    if not base:
        raise HTTPException(status_code=404, detail="reference embedding not found")
    results = emb.search_similar(db, req.namespace, base.embedding, req.k)
    items = [schemas.RecommendItem(**r) for r in results if r["ref_id"] != req.ref_id]
    return schemas.RecommendResponse(items=items)
