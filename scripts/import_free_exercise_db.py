"""
Import exercises from yuhonas/free-exercise-db (GitHub) into exercise_catalog.

Default source:
  https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json

Usage:
  python scripts/import_free_exercise_db.py
  python scripts/import_free_exercise_db.py --url <json-url>
  python scripts/import_free_exercise_db.py --path /path/to/exercises.json

Notes:
  - Picks the first image from 'images' and prefixes with the repo base to build demo_url.
  - Skips duplicates by name.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy import select, inspect

from app.core.database import SessionLocal
from app.auth import models as _auth_models  # noqa: F401
from app.user_profile import models as _profile_models  # noqa: F401
from app.routines.models import ExerciseCatalog


DEFAULT_URL = (
    "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
)
IMG_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"


def _load_data(url: Optional[str], path: Optional[Path]) -> List[Dict[str, Any]]:
    if url:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise ValueError("Remote JSON should be a list of exercises")
        return data
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Local JSON should be a list of exercises")
        return data
    raise ValueError("Either url or path must be provided")


def _first_image_url(images: List[str] | None) -> Optional[str]:
    if not images:
        return None
    img = images[0]
    if img.startswith("http://") or img.startswith("https://"):
        return img
    return IMG_BASE + img


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
    name = (row.get("name") or "").lower()
    if name in _NAME_ES:
        out["name"] = _NAME_ES[name]
    cat = (row.get("category") or "").lower()
    if cat in _MUSCLE_ES:
        out["category"] = _MUSCLE_ES[cat]
    mg = row.get("muscle_groups") or []
    out["muscle_groups"] = [
        _MUSCLE_ES.get((m or "").lower(), m) for m in mg if m
    ] or None
    eq = (row.get("equipment") or "").lower()
    if eq in _EQUIP_ES:
        out["equipment"] = _EQUIP_ES[eq]
    # Level
    lvl = (row.get("level") or "").lower()
    level_map = {
        "beginner": "principiante",
        "novice": "principiante",
        "intermediate": "intermedio",
        "advanced": "experto",
        "expert": "experto",
        "avanzado": "experto",
    }
    if lvl in level_map:
        out["level"] = level_map[lvl]
    return out


def import_free_exercise_db(url: Optional[str] = DEFAULT_URL, path: Optional[str] = None, dry_run: bool = False, translate_es: bool = False, update_existing: bool = False) -> int:
    pdata = _load_data(url, Path(path) if path else None)
    added = 0

    with SessionLocal() as db:
        insp = inspect(db.bind)
        if not insp.has_table("exercise_catalog"):
            raise RuntimeError("exercise_catalog no existe. Ejecuta 'alembic upgrade head' en el contenedor web.")
        # name -> id map for quick existing lookup
        existing_rows = db.execute(select(ExerciseCatalog.id, ExerciseCatalog.name)).all()
        existing = {name: _id for (_id, name) in existing_rows}
        for ex in pdata:
            name = (ex.get("name") or "").strip()
            if not name:
                continue
            category = (ex.get("category") or None)
            equipment = (ex.get("equipment") or None)
            level = (ex.get("level") or None)
            muscle_groups = (ex.get("primaryMuscles") or []) + (ex.get("secondaryMuscles") or [])
            if muscle_groups:
                muscle_groups = [m for m in muscle_groups if m]
            else:
                muscle_groups = None
            images = ex.get("images")
            demo_url = _first_image_url(images)
            description = None
            instr = ex.get("instructions")
            if isinstance(instr, list):
                description = "\n".join(str(s) for s in instr if s)
            elif isinstance(instr, str):
                description = instr

            row_dict = dict(
                name=name,
                category=category,
                equipment=equipment,
                description=description,
                level=level,
                muscle_groups=muscle_groups,
                media_url=demo_url,
                demo_url=demo_url,
            )
            if translate_es:
                row_dict = _translate_es(row_dict)
            if name in existing:
                if update_existing and not dry_run:
                    # update selected fields on existing row
                    obj = db.get(ExerciseCatalog, existing[name])
                    if obj:
                        obj.category = row_dict.get("category") or obj.category
                        obj.equipment = row_dict.get("equipment") or obj.equipment
                        obj.level = row_dict.get("level") or obj.level
                        obj.muscle_groups = row_dict.get("muscle_groups") or obj.muscle_groups
                        obj.media_url = row_dict.get("media_url") or obj.media_url
                        obj.demo_url = row_dict.get("demo_url") or obj.demo_url
                        # description is optional; only set if not present
                        if not obj.description and row_dict.get("description"):
                            obj.description = row_dict.get("description")
                # count as processed, not added
                continue
            else:
                row = ExerciseCatalog(**row_dict)
                if dry_run:
                    added += 1
                    continue
                db.add(row)
                added += 1
        if not dry_run:
            db.commit()
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description="Import free-exercise-db JSON")
    ap.add_argument("--url", default=DEFAULT_URL, help="JSON URL (default: dist/exercises.json)")
    ap.add_argument("--path", default=None, help="Local path to exercises.json (overrides url)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--translate-es", action="store_true")
    ap.add_argument("--update-existing", action="store_true")
    args = ap.parse_args()

    added = import_free_exercise_db(url=None if args.path else args.url, path=args.path, dry_run=args.dry_run, translate_es=args.translate_es, update_existing=args.update_existing)
    print(f"Imported {added} exercises")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
