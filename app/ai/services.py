"""Business logic for the AI endpoints."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai_client import get_ai_client
from app.auth.deps import UserContext
from app.user_profile.models import UserProfile
from app.nutrition import services as nutrition_services

from . import embeddings as emb
from . import schemas

# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


# --- Helpers de mapeo a español --------------------------------------------
def _es_goal(value: object | None) -> str | None:
    if value is None:
        return None
    raw = getattr(value, "value", value)
    mapping = {
        "lose_weight": "perder peso",
        "maintain_weight": "mantener peso",
        "gain_weight": "ganar peso",
    }
    return mapping.get(str(raw), str(raw))


def _es_activity(value: object | None) -> str | None:
    if value is None:
        return None
    raw = getattr(value, "value", value)
    mapping = {
        "sedentary": "sedentario",
        "lightly_active": "ligera",
        "moderately_active": "moderada",
        "very_active": "activa",
        "extra_active": "muy activa",
    }
    return mapping.get(str(raw), str(raw))


def _es_equipment_access(value: str | None) -> str | None:
    if value is None:
        return None
    mapping = {
        "none": "sin equipamiento",
        "basic": "básico",
        "full_gym": "gimnasio completo",
    }
    return mapping.get(value, value)


def _es_diet(value: str | None) -> str | None:
    if value is None:
        return None
    mapping = {
        "omnivore": "omnívoro",
        "vegetarian": "vegetariano",
        "vegan": "vegano",
        "pescatarian": "pescetariano",
        "keto": "keto",
        "none": "ninguna",
    }
    return mapping.get(value, value)


def _es_sex(value: str | None) -> str | None:
    if value is None:
        return None
    mapping = {
        "male": "hombre",
        "female": "mujer",
        "other": "otro",
    }
    return mapping.get(value, value)


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
    user: UserContext,
    req: schemas.WorkoutPlanRequest,
    db: Session,
    *,
    simulate: bool = False,
) -> schemas.WorkoutPlan:
    """Generate a workout plan via AI or return a deterministic stub when simulating."""
    # Perfil (para posibles fallbacks)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    # Detectar si el cliente envió explícitamente days_per_week
    provided_fields = req.model_dump(exclude_unset=True)
    days_per_week_value = req.days_per_week
    if "days_per_week" not in provided_fields and profile and isinstance(
        profile.training_days_per_week, int
    ):
        # Normalizar a 1..7
        dpw = max(1, min(7, int(profile.training_days_per_week)))
        days_per_week_value = dpw

    from app.core.config import settings as _settings  # local import to avoid cycles
    if simulate or not _settings.OPENROUTER_KEY:
        def _weekday_name(idx: int) -> str:
            names = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            return names[max(0, min(6, idx))]

        chosen = req.preferred_days or list(range(days_per_week_value))
        days: list[schemas.WorkoutPlanDay] = []
        count = max(1, days_per_week_value)
        for i in range(count):
            wd = chosen[i % len(chosen)] if chosen else i
            days.append(
                schemas.WorkoutPlanDay(
                    weekday=_weekday_name(wd),
                    focus="full body",
                    exercises=[
                        schemas.WorkoutExercise(
                            name="push up", sets=3, reps=10, rest_sec=60
                        ),
                    ],
                )
            )
        return schemas.WorkoutPlan(
            name="Plan",
            days_per_week=days_per_week_value,
            days=days,
            constraints={},
            total_time_min=45,
        )

    client = get_ai_client()
    sys_prompt = (
        "Eres PlanifitAI, un asistente de fitness. Devuelve únicamente JSON válido, sin explicaciones. "
        "Esquema: {name: str, days_per_week: int, days: [{weekday: str, focus?: str, exercises: [{name: str, sets: int, reps: int, rest_sec?: int, notes?: str}]}], constraints?: {str:str}, total_time_min?: int}."
    )
    preferred_days_txt = (
        ", ".join(str(d) for d in (req.preferred_days or [])) if req.preferred_days else None
    )
    per_day_eq_txt = None
    if req.equipment_by_day:
        # Render mapping as human-readable pairs (e.g., 0:["mancuernas","barra"])
        items = []
        for k in sorted(req.equipment_by_day.keys()):
            v = ", ".join(req.equipment_by_day[k])
            items.append(f"{k}:[{v}]")
        per_day_eq_txt = "; ".join(items)
    injuries_txt = ", ".join(req.injuries or []) if req.injuries else None
    # Enriquecer con datos de perfil si existen (perfil ya consultado)
    profile_ctx_parts: list[str] = []
    if profile:
        # Identidad y biometría básica
        if profile.sex:
            profile_ctx_parts.append(f"sexo={_es_sex(profile.sex)}")
        if isinstance(profile.age, int):
            profile_ctx_parts.append(f"edad={profile.age}")
        if profile.height_cm is not None:
            profile_ctx_parts.append(f"altura_cm={float(profile.height_cm):.0f}")
        if profile.weight_kg is not None:
            profile_ctx_parts.append(f"peso_kg={float(profile.weight_kg):.1f}")
        # Objetivo y actividad
        if profile.goal:
            profile_ctx_parts.append(f"objetivo={_es_goal(profile.goal)}")
        if profile.activity_level:
            profile_ctx_parts.append(f"actividad={_es_activity(profile.activity_level)}")
        # Preferencias de planificación
        if isinstance(profile.training_days_per_week, int):
            profile_ctx_parts.append(
                f"dias_entrenamiento_semana={profile.training_days_per_week}"
            )
        if isinstance(profile.time_per_session_min, int):
            profile_ctx_parts.append(
                f"minutos_por_sesion={profile.time_per_session_min}"
            )
        if profile.equipment_access:
            profile_ctx_parts.append(
                f"equipamiento={_es_equipment_access(profile.equipment_access)}"
            )
        # Condiciones médicas y alergias
        if profile.medical_conditions:
            profile_ctx_parts.append(
                f"condiciones_medicas={profile.medical_conditions}"
            )
        if profile.allergies:
            profile_ctx_parts.append(f"alergias={profile.allergies}")

    profile_ctx = f" Perfil: {'; '.join(profile_ctx_parts)}. " if profile_ctx_parts else ""

    # Fallback de equipamiento general: si no viene en la petición, usar el del perfil
    equipment_general = (
        req.equipment
        if (getattr(req, "equipment", None) and str(req.equipment).strip())
        else (_es_equipment_access(profile.equipment_access) if (profile and profile.equipment_access) else "ninguno")
    )

    user_prompt = (
        f"Genera un plan de entrenamiento personalizado en español. Días/semana: {days_per_week_value}. "
        f"Equipo general disponible: {equipment_general}. Preferencias: {req.preferences or {}}. "
        + (f"Días preferidos (0=lunes..6=domingo): [{preferred_days_txt}]. " if preferred_days_txt else "")
        + (f"Equipo por día (0..6): {per_day_eq_txt}. " if per_day_eq_txt else "")
        + (f"Lesiones/restricciones: {injuries_txt}. " if injuries_txt else "")
        + profile_ctx
        + "No devuelvas texto fuera del JSON."
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
    user: UserContext,
    req: schemas.NutritionPlanRequest,
    db: Session,
    *,
    simulate: bool = False,
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
    # Enriquecer con datos del perfil y objetivos sugeridos
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    profile_ctx_parts: list[str] = []
    suggested_targets_txt = None
    if profile:
        if profile.sex:
            profile_ctx_parts.append(f"sexo={_es_sex(profile.sex)}")
        if isinstance(profile.age, int):
            profile_ctx_parts.append(f"edad={profile.age}")
        if profile.height_cm is not None:
            profile_ctx_parts.append(f"altura_cm={float(profile.height_cm):.0f}")
        if profile.weight_kg is not None:
            profile_ctx_parts.append(f"peso_kg={float(profile.weight_kg):.1f}")
        if profile.goal:
            profile_ctx_parts.append(f"objetivo={_es_goal(profile.goal)}")
        if profile.activity_level:
            profile_ctx_parts.append(f"actividad={_es_activity(profile.activity_level)}")
        if profile.dietary_preference:
            profile_ctx_parts.append(
                f"preferencia_dietetica={_es_diet(profile.dietary_preference)}"
            )
        if profile.allergies:
            profile_ctx_parts.append(f"alergias={profile.allergies}")
        if profile.medical_conditions:
            profile_ctx_parts.append(
                f"condiciones_medicas={profile.medical_conditions}"
            )
        # Calcular objetivos sugeridos para guiar a la IA
        try:
            auto = nutrition_services.compute_auto_targets(profile)
            # convertir Decimals a float para una representación más limpia
            kcal = int(auto.get("calories_target") or 0)
            pg = float(auto.get("protein_g_target") or 0)
            cg = float(auto.get("carbs_g_target") or 0)
            fg = float(auto.get("fat_g_target") or 0)
            suggested_targets_txt = (
                f"kcal={kcal}, protein_g={pg:.2f}, carbs_g={cg:.2f}, fat_g={fg:.2f}"
            )
        except Exception:
            suggested_targets_txt = None

    profile_ctx = f" Perfil: {'; '.join(profile_ctx_parts)}. " if profile_ctx_parts else ""
    targets_ctx = (
        f" Objetivos sugeridos: {{{suggested_targets_txt}}}. "
        if suggested_targets_txt
        else ""
    )

    user_prompt = (
        f"Genera un plan de nutrición de {len(dates)} días en español para las fechas {dates}. "
        f"Preferencias/restricciones: {req.preferences or {}}."
        + profile_ctx
        + targets_ctx
        + " Usa unidades simples (g, ml, unidad). No devuelvas texto fuera del JSON."
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
