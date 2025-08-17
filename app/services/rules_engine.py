# app/services/rules_engine.py
import json
from copy import deepcopy
from pathlib import Path

# Lista de palabras que indican saltos/impacto
IMPACT_WORDS = {"burpee", "salto", "jump", "jumping", "plyo"}
# Alternativas seguras cuando hay problemas de rodilla
SAFE_ALTERNATIVES = {
    "burpee": "puente de glúteo",
    "salto": "sentadilla sin salto",
    "jump": "sentadilla sin salto",
    "jumping": "sentadilla sin salto",
    "plyo": "zancadas estáticas",
}


_TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "models" / "templates.json"
with _TEMPLATES_PATH.open(encoding="utf-8") as fh:
    _TEMPLATES = json.load(fh)


def validate_frequency(freq: int) -> None:
    if not (2 <= freq <= 6):
        raise ValueError(
            "PLAN_INVALID_FREQ: Frecuencia fuera de rango (usa 2 a 6 días)."
        )


def apply_restrictions(plan_dict: dict, restrictions: list[str]) -> dict:
    """
    Si el usuario indica 'rodilla' en restricciones, evitamos ejercicios de salto/impacto.
    """
    plan = deepcopy(plan_dict)
    needs_knee_care = any("rodilla" in r.lower() for r in (restrictions or []))

    if not needs_knee_care:
        return plan

    for day in plan.get("structure", []):
        cleaned = []
        for ex in day.get("exercises", []):
            ex_low = ex.lower()
            if any(w in ex_low for w in IMPACT_WORDS):
                # Reemplaza por alternativa segura
                replaced = None
                for w in IMPACT_WORDS:
                    if w in ex_low and w in SAFE_ALTERNATIVES:
                        replaced = SAFE_ALTERNATIVES[w]
                        break
                cleaned.append(replaced or "puente de glúteo")
            else:
                cleaned.append(ex)
        day["exercises"] = cleaned
    return plan


def ensure_structure(
    objective_key: str, base_template: dict, requested_freq: int
) -> dict:
    """
    Ajusta la plantilla si el usuario pide más/menos días:
    - Si pide menos: recorta.
    - Si pide más: repite días de forma sencilla.
    """
    plan = deepcopy(base_template)
    current = plan.get("structure", [])
    if not current:
        raise ValueError("PLAN_INVALID_TEMPLATE: Plantilla vacía.")

    if requested_freq == len(current):
        return plan

    if requested_freq < len(current):
        plan["structure"] = current[:requested_freq]
        plan["days"] = requested_freq
        return plan

    # requested_freq > len(current): duplicamos de forma simple para completar
    i = 0
    while len(current) < requested_freq:
        # copia del día i con número de día actualizado
        next_day = deepcopy(current[i % len(current)])
        next_day["day"] = len(current) + 1
        current.append(next_day)
        i += 1
    plan["structure"] = current
    plan["days"] = requested_freq
    return plan


def select_template(objective: str, frequency: int) -> dict | None:
    mapping = {"strength": f"strength_{frequency}days"}
    key = mapping.get(objective)
    if not key:
        return None
    tpl = _TEMPLATES.get(key)
    return deepcopy(tpl) if tpl else None


def scale_volume(structure: list, level: str, session_minutes: int) -> list:
    scaled: list = []
    base_sets = 3
    if level == "beginner":
        sets = max(1, base_sets - 1)
        max_exercises = 3
    elif level == "advanced":
        sets = min(5, base_sets + 1)
        max_exercises = 5
    else:
        sets = base_sets
        max_exercises = 4

    for day in structure:
        exercises = day.get("exercises", [])
        if session_minutes < 25 and len(exercises) > 1:
            exercises = exercises[:-1]
        exercises = exercises[:max_exercises]
        ex_objs = [
            {"name": ex, "sets": sets, "reps": 10, "seconds": None} for ex in exercises
        ]
        scaled.append({"day": day.get("day"), "exercises": ex_objs})
    return scaled


def progression_week(structure: list, level: str) -> list:
    progressed = deepcopy(structure)
    if level == "advanced" and progressed:
        last_day = progressed[-1]
        exercises = last_day.get("exercises", [])
        if exercises:
            last_ex = exercises[-1]
            last_ex["sets"] = min(5, (last_ex.get("sets") or 1) + 1)
    return progressed
