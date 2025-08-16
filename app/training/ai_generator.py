from copy import deepcopy


def generate(plan: dict) -> dict:
    """Stub de generador IA: añade un campo nota."""
    enriched = deepcopy(plan)
    enriched["note"] = "IA pendiente"
    return enriched
