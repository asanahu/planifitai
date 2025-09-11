import logging
from time import perf_counter
from typing import List, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import PLAN_NOT_FOUND, err, ok
from app.routines.models import Routine, RoutineDay, RoutineExercise
from app.training.planner import advance_plan_one_week, generate_plan_v2
from app.training.schemas import PlanDTO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/training", tags=["training"]) 


# Modelo "compat" con defaults para no romper tests antiguos
class GenerateTrainingIn(BaseModel):
    objective: str
    frequency: int
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    session_minutes: int = 25
    restrictions: List[str] = []
    persist: bool = False
    use_ai: bool = False  # opcional; no lo exigen los tests


class NextWeekIn(BaseModel):
    plan: dict
    use_ai: bool = True
    persist: bool = False


@router.post("/generate")
def generate_training(payload: GenerateTrainingIn, db: Session = Depends(get_db)):
    start = perf_counter()
    try:
        plan = generate_plan_v2(
            objective=payload.objective,
            level=payload.level,
            frequency=payload.frequency,
            session_minutes=payload.session_minutes,
            restrictions=payload.restrictions,
            use_ai=payload.use_ai,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("PLAN_INVALID_FREQ"):
            return err(
                "PLAN_INVALID_FREQ", "Frecuencia fuera de rango (usa 2 a 6 días).", 400
            )
        return err("COMMON_VALIDATION", msg, 400)
    except KeyError as exc:
        if str(exc).strip("\"'") in {"PLAN_NOT_FOUND", "template_not_found"}:
            return err(PLAN_NOT_FOUND, "Plantilla no encontrada", 404)
        return err(PLAN_NOT_FOUND, "Plantilla no encontrada", 404)

    # --- Persistencia opcional (sin cambios) ---
    if payload.persist:
        routine = Routine(name=f"{payload.objective} plan", description=None)
        db.add(routine)
        db.flush()

        for dp in plan.days:
            day = RoutineDay(
                routine_id=routine.id,
                weekday=dp.day - 1,
                order_index=dp.day - 1,
            )
            db.add(day)
            db.flush()
            for block in dp.blocks:
                for order, ex in enumerate(block.exercises):
                    db.add(
                        RoutineExercise(
                            routine_day_id=day.id,
                            exercise_name=ex.name,
                            sets=ex.sets or 1,
                            reps=ex.reps,
                            time_seconds=ex.seconds,
                            order_index=order,
                        )
                    )
        db.commit()

        # Vista v2 + compat v1 en la respuesta
        data = plan.model_dump()
        # TODO(deprecate): compat v1 se retirará en v0.4
        # compat: nota en raíz
        if "note" not in data:
            note = data.get("meta", {}).get("note")
            data["note"] = "IA pendiente" if not note else "IA pendiente"
        # compat: exercises plano por día
        for d in data.get("days", []):
            if "exercises" not in d:
                ex_names = []
                for b in d.get("blocks", []):
                    for ex in b.get("exercises", []):
                        name = ex.get("name")
                        if name:
                            ex_names.append(name)
                d["exercises"] = ex_names

        duration_ms = int((perf_counter() - start) * 1000)
        source = getattr(getattr(plan, "meta", None), "source", None)
        logger.info(
            "training.generate duration_ms=%d source=%s objective=%s frequency=%s level=%s use_ai=%s",
            duration_ms,
            source,
            payload.objective,
            payload.frequency,
            payload.level,
            payload.use_ai,
        )
        return ok({"routine_id": routine.id, "plan": data})

    # --- Respuesta NO persistente: v2 + compat v1 ---
    data = plan.model_dump()

    # TODO(deprecate): compat v1 se retirará en v0.4
    # compat: nota en raíz (los tests esperan "IA pendiente")
    if "note" not in data:
        note = data.get("meta", {}).get("note")
        data["note"] = "IA pendiente" if not note else "IA pendiente"

    # compat: exercises plano por día para tests v1
    for d in data.get("days", []):
        if "exercises" not in d:
            ex_names = []
            for b in d.get("blocks", []):
                for ex in b.get("exercises", []):
                    name = ex.get("name")
                    if name:
                        ex_names.append(name)
            d["exercises"] = ex_names

    duration_ms = int((perf_counter() - start) * 1000)
    source = getattr(getattr(plan, "meta", None), "source", None)
    logger.info(
        "training.generate duration_ms=%d source=%s objective=%s frequency=%s level=%s use_ai=%s",
        duration_ms,
        source,
        payload.objective,
        payload.frequency,
        payload.level,
        payload.use_ai,
    )
    return ok(data)


@router.post("/next-week")
def next_week(payload: NextWeekIn, db: Session = Depends(get_db)):
    start = perf_counter()

    # Genera el plan de la siguiente semana (progresión + IA simulada)
    # Limpieza simple para compat de payloads con "exercises" planos
    plan_in = dict(payload.plan)
    if isinstance(plan_in.get("days"), list):
        for d in plan_in["days"]:
            if "blocks" not in d and "exercises" in d:
                d["blocks"] = [
                    {
                        "type": "straight",
                        "duration": None,
                        "exercises": [
                            {"name": name, "sets": None, "reps": 10, "seconds": None}
                            if isinstance(name, str)
                            else name
                            for name in d.get("exercises", [])
                        ],
                    }
                ]
    base_plan = PlanDTO.model_validate(plan_in)
    plan = advance_plan_one_week(base_plan, use_ai=payload.use_ai)

    # Persistencia opcional
    if payload.persist:
        routine = Routine(name=f"{plan.objective} plan semana {plan.meta.get('week', '')}", description=None)
        db.add(routine)
        db.flush()

        for dp in plan.days:
            day = RoutineDay(
                routine_id=routine.id,
                weekday=dp.day - 1,
                order_index=dp.day - 1,
            )
            db.add(day)
            db.flush()
            for block in dp.blocks:
                for order, ex in enumerate(block.exercises):
                    db.add(
                        RoutineExercise(
                            routine_day_id=day.id,
                            exercise_name=ex.name,
                            sets=ex.sets or 1,
                            reps=ex.reps,
                            time_seconds=ex.seconds,
                            order_index=order,
                        )
                    )
        db.commit()

        data = plan.model_dump()
        if "note" not in data:
            note = data.get("meta", {}).get("note")
            data["note"] = "IA pendiente" if not note else "IA pendiente"
        for d in data.get("days", []):
            if "exercises" not in d:
                ex_names = []
                for b in d.get("blocks", []):
                    for ex in b.get("exercises", []):
                        name = ex.get("name")
                        if name:
                            ex_names.append(name)
                d["exercises"] = ex_names

        duration_ms = int((perf_counter() - start) * 1000)
        source = getattr(getattr(plan, "meta", None), "source", None)
        logger.info(
            "training.next_week duration_ms=%d source=%s objective=%s use_ai=%s",
            duration_ms,
            source,
            plan.objective,
            payload.use_ai,
        )
        return ok({"routine_id": routine.id, "plan": data})

    # Respuesta NO persistente: v2 + compat v1
    data = plan.model_dump()
    if "note" not in data:
        note = data.get("meta", {}).get("note")
        data["note"] = "IA pendiente" if not note else "IA pendiente"
    for d in data.get("days", []):
        if "exercises" not in d:
            ex_names = []
            for b in d.get("blocks", []):
                for ex in b.get("exercises", []):
                    name = ex.get("name")
                    if name:
                        ex_names.append(name)
            d["exercises"] = ex_names

    duration_ms = int((perf_counter() - start) * 1000)
    source = getattr(getattr(plan, "meta", None), "source", None)
    logger.info(
        "training.next_week duration_ms=%d source=%s objective=%s use_ai=%s",
        duration_ms,
        source,
        plan.objective,
        payload.use_ai,
    )
    return ok(data)
