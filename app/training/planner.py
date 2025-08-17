import json
from pathlib import Path
from typing import List

from app.services import rules_engine
from app.training.ai_generator import refine_with_ai
from app.training.schemas import Block, DayPlan, Exercise, Level, PlanDTO

_TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "models" / "templates.json"


def generate_plan(
    objective: str, frequency: int, restrictions: List[str] | None = None
) -> dict:
    """Genera un plan de entrenamiento a partir de las plantillas."""
    rules_engine.validate_frequency(frequency)

    with _TEMPLATES_PATH.open(encoding="utf-8") as fh:
        templates = json.load(fh)

    key_exact = f"{objective}_{frequency}days"
    key_default = f"{objective}_3days"
    base_template = templates.get(key_exact) or templates.get(key_default)
    if not base_template:
        raise KeyError("Plantilla no encontrada")

    plan = rules_engine.ensure_structure(objective, base_template, frequency)
    plan = rules_engine.apply_restrictions(plan, restrictions or [])

    return {"days": plan.get("structure", [])}


def generate_plan_v2(
    objective: str,
    level: str,
    frequency: int,
    session_minutes: int,
    restrictions: list[str],
    use_ai: bool = False,
) -> PlanDTO:
    rules_engine.validate_frequency(frequency)

    with _TEMPLATES_PATH.open(encoding="utf-8") as fh:
        json.load(fh)

    tpl = rules_engine.select_template(objective, frequency)
    if tpl is None:
        raise KeyError("PLAN_NOT_FOUND")

    base = rules_engine.ensure_structure(objective, tpl, frequency)
    base = rules_engine.apply_restrictions(base, restrictions)
    base["structure"] = rules_engine.scale_volume(
        base.get("structure", []), level, session_minutes
    )
    base["structure"] = rules_engine.progression_week(base.get("structure", []), level)

    days: list[DayPlan] = []
    for day in base.get("structure", []):
        exercises = [
            Exercise(**ex) if isinstance(ex, dict) else Exercise(name=str(ex))
            for ex in day.get("exercises", [])
        ]
        block = Block(type="straight", duration=None, exercises=exercises)
        days.append(DayPlan(day=day.get("day"), blocks=[block]))

    prelim = PlanDTO(
        objective=objective,
        level=Level(level),
        frequency=frequency,
        session_minutes=session_minutes,
        days=days,
        meta={},
    )

    final = prelim
    if use_ai:
        dto_dict = prelim.model_dump()
        context = {
            "objective": objective,
            "level": level,
            "session_minutes": session_minutes,
            "restrictions": restrictions,
        }
        refined = refine_with_ai(dto_dict, context)
        try:
            final = PlanDTO.model_validate(refined)
            final.meta.setdefault("source", "ai")
        except Exception:
            final = prelim
            final.meta.setdefault("source", "rules")
    else:
        final.meta.setdefault("source", "rules")

    final.meta.setdefault("warnings", [])
    return final
