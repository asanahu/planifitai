import json
from pathlib import Path
from typing import List

from app.services import rules_engine
from app.services.rules_engine import select_template
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

    tpl = select_template(objective, frequency)
    if tpl is None:
        # subir un KeyError claro para que el router lo capture
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


def advance_plan_one_week(prev: PlanDTO, use_ai: bool = True) -> PlanDTO:
    """Genera el plan de la siguiente semana a partir de un PlanDTO previo.

    Estrategia simple de progresión:
    - Si un ejercicio tiene ``sets``: +1 set hasta máximo 5.
    - Si tiene ``reps`` (y no tiene sets definidos): +1 rep (máx. 20).
    - Si tiene ``seconds``: +5s (máx. 120s).

    Luego, opcionalmente, se refina con IA (simulada) para variaciones menores.
    """
    progressed_days: list[DayPlan] = []

    for day in prev.days:
        new_blocks: list[Block] = []
        for block in day.blocks:
            new_exercises: list[Exercise] = []
            for ex in block.exercises:
                sets = ex.sets
                reps = ex.reps
                seconds = ex.seconds

                if sets is not None:
                    sets = min(5, (sets or 1) + 1)
                elif reps is not None:
                    reps = min(20, max(1, reps + 1))
                elif seconds is not None:
                    seconds = min(120, max(5, seconds + 5))

                new_exercises.append(
                    Exercise(name=ex.name, sets=sets, reps=reps, seconds=seconds)
                )

            new_blocks.append(
                Block(type=block.type, duration=block.duration, exercises=new_exercises)
            )

        progressed_days.append(DayPlan(day=day.day, blocks=new_blocks))

    prelim = PlanDTO(
        objective=prev.objective,
        level=prev.level,
        frequency=prev.frequency,
        session_minutes=prev.session_minutes,
        days=progressed_days,
        meta={**(prev.meta or {})},
    )

    # Actualiza meta con la semana
    week = 1
    try:
        week = int(prelim.meta.get("week", 1))
    except Exception:
        week = 1
    prelim.meta["week"] = week + 1

    final = prelim
    if use_ai:
        dto_dict = prelim.model_dump()
        context = {
            "objective": prelim.objective,
            "level": prelim.level.value if isinstance(prelim.level, Level) else str(prelim.level),
            "session_minutes": prelim.session_minutes,
            "restrictions": [],
            "week": prelim.meta.get("week"),
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
