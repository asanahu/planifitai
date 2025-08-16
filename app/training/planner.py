import json
from pathlib import Path
from typing import List

from app.services import rules_engine

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
