from __future__ import annotations

import json
from copy import deepcopy

from app.ai_client import get_ai_client
from app.training.schemas import PlanDTO


def generate(plan: dict) -> dict:
    """Stub de generador IA: añade un campo nota."""
    enriched = deepcopy(plan)
    enriched["note"] = "IA pendiente"
    return enriched


def refine_with_ai(plan_dict: dict, context: dict) -> dict:
    prompt = (
        "Genera un plan ajustado en JSON. Objetivo: {objective}. Nivel: {level}. "
        "Sesión: {minutes} minutos. Restricciones: {restrictions}. "
        "Responde SOLO con JSON que siga el esquema PlanDTO."
    ).format(
        objective=context.get("objective"),
        level=context.get("level"),
        minutes=context.get("session_minutes"),
        restrictions=", ".join(context.get("restrictions") or []),
    )

    try:
        client = get_ai_client()
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat(0, messages, simulate=True)
        content = resp.get("content") or resp.get("message", {}).get("content", "")
        refined = json.loads(content)
        PlanDTO.model_validate(refined)
        return refined
    except Exception:
        fallback = deepcopy(plan_dict)
        meta = fallback.setdefault("meta", {})
        note = meta.get("note") or "AI simulate"
        meta["note"] = "AI fallback" if note != "AI simulate" else note
        return fallback
