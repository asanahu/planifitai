"""
Import exercises from the Wger API into exercise_catalog.

Requires:
  - DATABASE_URL configured
  - WGER_API_TOKEN in environment or pass --token

Usage examples:
  python scripts/import_wger.py --language es
  python scripts/import_wger.py --language es --token YOURTOKEN

Notes:
  - This script fetches exercises with status=2 (verified), in the selected language.
  - It also fetches equipment, muscles and categories to map IDs to names.
  - If an exercise name already exists, it is skipped (no update overwrite).
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict, Iterable, List, Optional

import requests
from sqlalchemy import select, inspect

from app.core.config import settings
from app.core.database import SessionLocal
# Ensure all mappers are registered (Routine has relationship('User'))
from app.auth import models as _auth_models  # noqa: F401
from app.user_profile import models as _profile_models  # noqa: F401
from app.routines.models import ExerciseCatalog


BASE_URL = "https://wger.de/api/v2"


def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {"Accept": "application/json"}
    tok = token or settings.WGER_API_TOKEN
    if tok:
        headers["Authorization"] = f"Token {tok}"
    return headers


def _get_all(endpoint: str, params: Dict[str, Any], headers: Dict[str, str]) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/{endpoint.strip('/')}/"
    out: List[Dict[str, Any]] = []
    while url:
        resp = requests.get(url, params=params if "?" not in url else None, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") if isinstance(data, dict) else None
        if results is None:
            # Non-paginated endpoint
            if isinstance(data, dict):
                out.append(data)
            elif isinstance(data, list):
                out.extend(data)
            break
        out.extend(results)
        url = data.get("next")
        params = {}  # subsequent pages embed query in 'next'
    return out


def _map_dict(items: Iterable[Dict[str, Any]]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for it in items:
        _id = it.get("id")
        name = (it.get("name") or "").strip()
        if isinstance(_id, int) and name:
            out[_id] = name
    return out


def _get_image_for_exercise(exercise_id: int, headers: Dict[str, str]) -> Optional[str]:
    try:
        items = _get_all("exerciseimage", {"exercise": exercise_id, "limit": 10}, headers)
    except Exception:
        return None
    if not items:
        return None
    # Prefer main image if available
    main = next((i for i in items if i.get("is_main")), None)
    img = main or items[0]
    # Wger returns 'image' path; it is usually an absolute URL
    return img.get("image") or img.get("image_original")


def import_wger(language: str = "es", token: Optional[str] = None, dry_run: bool = False) -> int:
    headers = _auth_headers(token)

    equipment = _map_dict(_get_all("equipment", {"limit": 500}, headers))
    muscles = _map_dict(_get_all("muscle", {"limit": 500}, headers))
    categories = _map_dict(_get_all("exercisecategory", {"limit": 500}, headers))

    # Fetch exercises (verified)
    exercises = _get_all(
        "exercise",
        {"language": language, "status": 2, "limit": 100},
        headers,
    )

    # Prepare DB
    added = 0
    with SessionLocal() as db:
        insp = inspect(db.bind)
        if not insp.has_table("exercise_catalog"):
            raise RuntimeError("exercise_catalog no existe. Ejecuta 'alembic upgrade head' en el contenedor web.")
        existing_names = set(n for (n,) in db.execute(select(ExerciseCatalog.name)).all() if n)

        for ex in exercises:
            name = (ex.get("name") or "").strip()
            if not name or name in existing_names:
                continue
            # category: id -> name
            cat_id = ex.get("category") if isinstance(ex.get("category"), int) else None
            category = categories.get(cat_id) if cat_id else None

            # equipment: list of ids -> first (or joined)
            eq = ex.get("equipment") or []
            eq_names = [equipment.get(eid) for eid in eq if isinstance(eid, int)]
            equipment_name = (eq_names[0] or "").lower() if eq_names else None

            # muscles: primary + secondary -> names
            m1 = ex.get("muscles") or []
            m2 = ex.get("muscles_secondary") or []
            muscle_groups = [muscles.get(mid) for mid in (m1 + m2) if isinstance(mid, int)]
            muscle_groups = [m for m in muscle_groups if m]

            # description
            description = (ex.get("description") or None)

            # image
            demo_url = _get_image_for_exercise(ex.get("id"), headers)

            row = ExerciseCatalog(
                name=name,
                category=(category or None),
                equipment=equipment_name,
                description=description,
                level=None,
                muscle_groups=muscle_groups or None,
                media_url=demo_url,
                demo_url=demo_url,
            )
            if dry_run:
                added += 1
                continue
            db.add(row)
            added += 1
        if not dry_run:
            db.commit()
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description="Import exercises from Wger API")
    ap.add_argument("--language", default="es", help="Language code (default: es)")
    ap.add_argument("--token", default=None, help="Wger API token (overrides env)")
    ap.add_argument("--dry-run", action="store_true", help="Don't write to DB")
    args = ap.parse_args()

    added = import_wger(language=args.language, token=args.token, dry_run=args.dry_run)
    print(f"Imported {added} exercises")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
