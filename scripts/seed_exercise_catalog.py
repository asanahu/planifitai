"""
Seed the exercise_catalog table from a JSON dataset.

Usage:
  python scripts/seed_exercise_catalog.py path/to/exercises.json [--translate-es]

Accepted JSON shapes (examples):
  - ExerciseDB: [{"name": "push up", "bodyPart": "chest", "target": "pectorals", "equipment": "body weight", "gifUrl": "...", "secondaryMuscles": ["triceps"]}, ...]
  - Custom: [{"name": str, "category": str, "equipment": str, "level": str, "muscle_groups": [str], "demo_url": str, "media_url": str, "description": str}]

Environment:
  Requires DATABASE_URL in .env or environment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from sqlalchemy import select

from app.core.database import SessionLocal
from app.routines.models import ExerciseCatalog


def _norm_str(s: Any | None) -> str | None:
    return str(s).strip() if s is not None else None


def _from_exercisedb(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm_str(payload.get("name"))
    category = _norm_str(payload.get("target")) or _norm_str(payload.get("bodyPart"))
    equipment = _norm_str(payload.get("equipment"))
    demo = _norm_str(payload.get("gifUrl"))
    secondaries = payload.get("secondaryMuscles") or []
    muscles = [m.lower() for m in ([payload.get("target")] + secondaries) if m]
    return {
        "name": name.title() if name else None,
        "category": (category or "").lower() or None,
        "equipment": (equipment or "").lower() or None,
        "description": None,
        "level": None,
        "muscle_groups": muscles or None,
        "media_url": demo,
        "demo_url": demo,
    }


def _from_custom(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": _norm_str(payload.get("name")),
        "category": _norm_str(payload.get("category")),
        "equipment": _norm_str(payload.get("equipment")),
        "description": _norm_str(payload.get("description")),
        "level": _norm_str(payload.get("level")),
        "muscle_groups": payload.get("muscle_groups"),
        "media_url": _norm_str(payload.get("media_url")),
        "demo_url": _norm_str(payload.get("demo_url")),
    }


def _detect_shape(item: Dict[str, Any]) -> str:
    if {"gifUrl", "bodyPart", "target", "equipment"} & set(item.keys()):
        return "exercisedb"
    return "custom"


def _iter_normalized(items: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for it in items:
        kind = _detect_shape(it)
        out = _from_exercisedb(it) if kind == "exercisedb" else _from_custom(it)
        if out.get("name"):
            yield out


# --- Optional ES translation -------------------------------------------------
_MUSCLE_ES = {
    "chest": "pecho",
    "pectorals": "pectorales",
    "back": "espalda",
    "lats": "dorsales",
    "traps": "trapecios",
    "shoulders": "hombros",
    "delts": "deltoides",
    "biceps": "bíceps",
    "triceps": "tríceps",
    "forearms": "antebrazos",
    "abs": "abdominales",
    "core": "core",
    "obliques": "oblicuos",
    "glutes": "glúteos",
    "quads": "cuádriceps",
    "hamstrings": "isquiotibiales",
    "calves": "gemelos",
}

_EQUIP_ES = {
    "body weight": "peso corporal",
    "bodyweight": "peso corporal",
    "barbell": "barra",
    "dumbbell": "mancuernas",
    "kettlebell": "kettlebell",
    "machine": "máquina",
    "smith machine": "máquina smith",
    "cable": "polea",
    "resistance band": "banda elástica",
    "band": "banda elástica",
    "medicine ball": "balón medicinal",
    "ez bar": "barra z",
}

_NAME_ES = {
    "push up": "flexiones",
    "push-up": "flexiones",
    "pull up": "dominadas",
    "chin up": "dominadas supinas",
    "squat": "sentadilla",
    "front squat": "sentadilla frontal",
    "lunge": "zancadas",
    "bench press": "press de banca",
    "incline bench press": "press de banca inclinado",
    "overhead press": "press militar",
    "shoulder press": "press hombros",
    "deadlift": "peso muerto",
    "romanian deadlift": "peso muerto rumano",
    "barbell row": "remo con barra",
    "bent over row": "remo inclinado",
    "dumbbell row": "remo con mancuernas",
    "plank": "plancha",
    "crunch": "crunch",
    "sit up": "abdominales",
    "hip thrust": "elevación de cadera",
    "leg press": "prensa de piernas",
    "calf raise": "elevación de gemelos",
    "bicep curl": "curl de bíceps",
    "tricep extension": "extensión de tríceps",
    "lateral raise": "elevación lateral",
    "face pull": "face pull",
}


def _translate_es(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    # Nombre
    name = (row.get("name") or "").lower()
    if name in _NAME_ES:
        out["name"] = _NAME_ES[name]
    # Category
    cat = (row.get("category") or "").lower()
    if cat in _MUSCLE_ES:
        out["category"] = _MUSCLE_ES[cat]
    # Grupos musculares
    mg = row.get("muscle_groups") or []
    out["muscle_groups"] = [
        _MUSCLE_ES.get((m or "").lower(), m) for m in mg if m
    ] or None
    # Equipo
    eq = (row.get("equipment") or "").lower()
    if eq in _EQUIP_ES:
        out["equipment"] = _EQUIP_ES[eq]
    return out


def seed_from_json(path: Path, dry_run: bool = False, translate_es: bool = False) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of exercises")
    rows = list(_iter_normalized(data))
    if translate_es:
        rows = [_translate_es(r) for r in rows]
    added = 0
    with SessionLocal() as db:
        existing_names = set(
            n for (n,) in db.execute(select(ExerciseCatalog.name)).all() if n
        )
        for r in rows:
            if r["name"] in existing_names:
                continue
            if dry_run:
                added += 1
                continue
            db.add(ExerciseCatalog(**r))
            added += 1
        if not dry_run:
            db.commit()
    return added


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python scripts/seed_exercise_catalog.py path/to/exercises.json [--translate-es]")
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2
    translate = "--translate-es" in argv[2:]
    added = seed_from_json(path, translate_es=translate)
    print(f"Inserted {added} exercises")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
