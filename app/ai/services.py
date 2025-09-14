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
from . import prompt_library

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
    # Forzar modo simulado si está habilitado el modo desarrollo
    force_simulate = getattr(_settings, 'FORCE_SIMULATE_MODE', False)
    if simulate or force_simulate:
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


def generate_nutrition_plan_optimized(
    user: UserContext,
    req: schemas.NutritionPlanRequest,
    db: Session,
    *,
    simulate: bool = False,
) -> schemas.NutritionPlan:
    """Versión optimizada para generación rápida."""
    from app.core.config import settings as _settings
    # Forzar modo simulado si está habilitado el modo desarrollo
    force_simulate = getattr(_settings, 'FORCE_SIMULATE_MODE', False)
    if simulate or force_simulate:
        # Crear plan simulado más realista
        from datetime import timedelta
        
        days = []
        today = date.today()
        
        for i in range(max(1, req.days)):
            current_date = today + timedelta(days=i)
            
            # Desayuno
            breakfast_items = [
                schemas.MealItem(name="avena con leche", qty=50, unit="g", kcal=180, protein_g=6, carbs_g=30, fat_g=3),
                schemas.MealItem(name="plátano", qty=1, unit="unidad", kcal=90, protein_g=1, carbs_g=23, fat_g=0.3),
            ]
            breakfast = schemas.Meal(type="breakfast", items=breakfast_items, meal_kcal=270)
            
            # Almuerzo
            lunch_items = [
                schemas.MealItem(name="pechuga de pollo", qty=150, unit="g", kcal=250, protein_g=46, carbs_g=0, fat_g=5),
                schemas.MealItem(name="arroz integral", qty=80, unit="g", kcal=280, protein_g=6, carbs_g=58, fat_g=2),
                schemas.MealItem(name="brócoli", qty=100, unit="g", kcal=35, protein_g=3, carbs_g=7, fat_g=0.4),
            ]
            lunch = schemas.Meal(type="lunch", items=lunch_items, meal_kcal=565)
            
            # Cena
            dinner_items = [
                schemas.MealItem(name="salmón", qty=120, unit="g", kcal=200, protein_g=24, carbs_g=0, fat_g=12),
                schemas.MealItem(name="ensalada mixta", qty=150, unit="g", kcal=50, protein_g=2, carbs_g=8, fat_g=1),
                schemas.MealItem(name="aceite de oliva", qty=10, unit="ml", kcal=90, protein_g=0, carbs_g=0, fat_g=10),
            ]
            dinner = schemas.Meal(type="dinner", items=dinner_items, meal_kcal=340)
            
            # Snack
            snack_items = [
                schemas.MealItem(name="yogur griego", qty=150, unit="g", kcal=130, protein_g=15, carbs_g=8, fat_g=4),
                schemas.MealItem(name="nueces", qty=15, unit="g", kcal=100, protein_g=2, carbs_g=2, fat_g=10),
            ]
            snack = schemas.Meal(type="snack", items=snack_items, meal_kcal=230)
            
            # Totales del día
            day_totals = {
                "kcal": 1405,
                "protein_g": 99,
                "carbs_g": 128,
                "fat_g": 35.7
            }
            
            day_plan = schemas.NutritionDayPlan(
                date=current_date.isoformat(),
                meals=[breakfast, lunch, dinner, snack],
                totals=day_totals
            )
            days.append(day_plan)
        
        return schemas.NutritionPlan(
            days=days,
            targets={"kcal": 2000, "protein_g": 150, "carbs_g": 250, "fat_g": 70},
        )

    client = get_ai_client()
    today = date.today()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(max(1, req.days))]
    
    # Prompt ultra-conciso para máxima velocidad
    sys_prompt = "Eres PlanifitAI. Genera plan nutricional en JSON: {days: [{date: str, meals: [{type: str, items: [{name: str, qty: float, unit: str, kcal: float, protein_g: float, carbs_g: float, fat_g: float}]}], totals: {kcal: float, protein_g: float, carbs_g: float, fat_g: float}}], targets: {kcal: float, protein_g: float, carbs_g: float, fat_g: float}}"
    
    # Perfil mínimo
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    profile_ctx = ""
    if profile:
        if profile.sex:
            profile_ctx += f"sexo={_es_sex(profile.sex)} "
        if isinstance(profile.age, int):
            profile_ctx += f"edad={profile.age} "
        if profile.goal:
            profile_ctx += f"objetivo={_es_goal(profile.goal)} "

    user_prompt = f"Plan {len(dates)} días para {dates}. {profile_ctx}Solo JSON."
    
    resp = client.chat(
        user.id,
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    data = _parse_json_payload(resp.get("reply", ""))
    data = _normalize_plan_data_shape(data)
    try:
        return schemas.NutritionPlan.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI nutrition validation failed: {exc}")


def generate_nutrition_plan(
    user: UserContext,
    req: schemas.NutritionPlanRequest,
    db: Session,
    *,
    simulate: bool = False,
) -> schemas.NutritionPlan:
    from app.core.config import settings as _settings  # local import to avoid cycles
    # Forzar modo simulado si está habilitado el modo desarrollo
    force_simulate = getattr(_settings, 'FORCE_SIMULATE_MODE', False)
    if simulate or force_simulate:
        # Crear plan simulado más realista
        from datetime import timedelta
        
        days = []
        today = date.today()
        
        for i in range(max(1, req.days)):
            current_date = today + timedelta(days=i)
            
            # Desayuno
            breakfast_items = [
                schemas.MealItem(name="avena con leche", qty=50, unit="g", kcal=180, protein_g=6, carbs_g=30, fat_g=3),
                schemas.MealItem(name="plátano", qty=1, unit="unidad", kcal=90, protein_g=1, carbs_g=23, fat_g=0.3),
            ]
            breakfast = schemas.Meal(type="breakfast", items=breakfast_items, meal_kcal=270)
            
            # Almuerzo
            lunch_items = [
                schemas.MealItem(name="pechuga de pollo", qty=150, unit="g", kcal=250, protein_g=46, carbs_g=0, fat_g=5),
                schemas.MealItem(name="arroz integral", qty=80, unit="g", kcal=280, protein_g=6, carbs_g=58, fat_g=2),
                schemas.MealItem(name="brócoli", qty=100, unit="g", kcal=35, protein_g=3, carbs_g=7, fat_g=0.4),
            ]
            lunch = schemas.Meal(type="lunch", items=lunch_items, meal_kcal=565)
            
            # Cena
            dinner_items = [
                schemas.MealItem(name="salmón", qty=120, unit="g", kcal=200, protein_g=24, carbs_g=0, fat_g=12),
                schemas.MealItem(name="ensalada mixta", qty=150, unit="g", kcal=50, protein_g=2, carbs_g=8, fat_g=1),
                schemas.MealItem(name="aceite de oliva", qty=10, unit="ml", kcal=90, protein_g=0, carbs_g=0, fat_g=10),
            ]
            dinner = schemas.Meal(type="dinner", items=dinner_items, meal_kcal=340)
            
            # Snack
            snack_items = [
                schemas.MealItem(name="yogur griego", qty=150, unit="g", kcal=130, protein_g=15, carbs_g=8, fat_g=4),
                schemas.MealItem(name="nueces", qty=15, unit="g", kcal=100, protein_g=2, carbs_g=2, fat_g=10),
            ]
            snack = schemas.Meal(type="snack", items=snack_items, meal_kcal=230)
            
            # Totales del día
            day_totals = {
                "kcal": 1405,
                "protein_g": 99,
                "carbs_g": 128,
                "fat_g": 35.7
            }
            
            day_plan = schemas.NutritionDayPlan(
                date=current_date.isoformat(),
                meals=[breakfast, lunch, dinner, snack],
                totals=day_totals
            )
            days.append(day_plan)
        
        return schemas.NutritionPlan(
            days=days,
            targets={"kcal": 2000, "protein_g": 150, "carbs_g": 250, "fat_g": 70},
        )

    client = get_ai_client()
    today = date.today()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(max(1, req.days))]
    sys_prompt = prompt_library.NUTRITION_PLAN_SYSTEM_PROMPT
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
        f"Plan nutricional {len(dates)} días para {dates}. "
        f"Preferencias: {req.preferences or {}}."
        + profile_ctx
        + targets_ctx
        + " Solo JSON."
    )
    resp = client.chat(
        user.id,
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    data = _parse_json_payload(resp.get("reply", ""))
    data = _normalize_plan_data_shape(data)
    try:
        return schemas.NutritionPlan.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI nutrition validation failed: {exc}")


def _normalize_plan_data_shape(raw: dict) -> dict:
    """Normaliza y completa campos faltantes del plan para cumplir el esquema.
    - Agrega meal_kcal si falta
    - Agrega totals por día si falta
    - Asegura números en items
    - Asegura targets si faltan
    """
    data = raw if isinstance(raw, dict) else {}
    days = data.get("days")
    if isinstance(days, list):
        for day in days:
            meals = day.get("meals") or []
            sum_kcal = 0.0
            sum_p = 0.0
            sum_c = 0.0
            sum_f = 0.0
            for meal in meals:
                items = meal.get("items") or []
                mkcal = 0.0
                for it in items:
                    try:
                        it["kcal"] = float(it.get("kcal", 0) or 0)
                        it["protein_g"] = float(it.get("protein_g", 0) or 0)
                        it["carbs_g"] = float(it.get("carbs_g", 0) or 0)
                        it["fat_g"] = float(it.get("fat_g", 0) or 0)
                    except Exception:
                        it["kcal"] = 0.0
                        it["protein_g"] = it.get("protein_g", 0) or 0
                        it["carbs_g"] = it.get("carbs_g", 0) or 0
                        it["fat_g"] = it.get("fat_g", 0) or 0
                    mkcal += it["kcal"]
                    sum_p += float(it.get("protein_g", 0) or 0)
                    sum_c += float(it.get("carbs_g", 0) or 0)
                    sum_f += float(it.get("fat_g", 0) or 0)
                if "meal_kcal" not in meal or meal.get("meal_kcal") is None:
                    meal["meal_kcal"] = round(mkcal, 2)
                sum_kcal += mkcal
            if "totals" not in day or not isinstance(day.get("totals"), dict):
                day["totals"] = {
                    "kcal": round(sum_kcal, 2),
                    "protein_g": round(sum_p, 2),
                    "carbs_g": round(sum_c, 2),
                    "fat_g": round(sum_f, 2),
                }
    if "targets" not in data or not isinstance(data.get("targets"), dict):
        first_totals = (days[0].get("totals") if isinstance(days, list) and days else {}) or {}
        data["targets"] = {
            "kcal": int(first_totals.get("kcal", 2000) or 2000),
            "protein_g": float(first_totals.get("protein_g", 120) or 120),
            "carbs_g": float(first_totals.get("carbs_g", 250) or 250),
            "fat_g": float(first_totals.get("fat_g", 70) or 70),
        }
    return data


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
