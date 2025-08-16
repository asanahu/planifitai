# app/services/rules_engine.py
from copy import deepcopy

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
