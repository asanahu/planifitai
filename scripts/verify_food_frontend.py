#!/usr/bin/env python3
"""
Frontend audit for food autocomplete integration (Python version).
Generates JSON report and a textual log, mirroring instrucciones.md requirements.

Usage: python scripts/verify_food_frontend.py
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path.cwd()
WEB_SRC = ROOT / 'web' / 'src'


def read_text_safe(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except Exception:
        return ''


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if re.search(r"\.(ts|tsx|js|jsx|mjs)$", name, re.I):
                out.append(Path(dirpath) / name)
    return out


def grep_with_lines(pattern: str | re.Pattern[str], file: Path):
    text = read_text_safe(file)
    lines = text.splitlines()
    if isinstance(pattern, str):
        pat = re.compile(re.escape(pattern))
    else:
        pat = pattern
    hits = []
    for i, line in enumerate(lines, 1):
        if pat.search(line):
            hits.append({"file": str(file), "line": i, "text": line.strip()})
    return hits


def main():
    all_src_files = walk_files(WEB_SRC)

    # 1) Component
    food_picker = WEB_SRC / 'components' / 'FoodPicker.tsx'
    component_found = food_picker.exists()

    # 2) Meals wiring
    meals_today = WEB_SRC / 'features' / 'nutrition' / 'MealsToday.tsx'
    wired_in_meals = 'FAIL'
    meals_imports = []
    if meals_today.exists():
        meals_imports = grep_with_lines(re.compile(r"FoodPicker"), meals_today)
        if meals_imports:
            wired_in_meals = 'PASS'

    # 3) API calls
    api_nutrition = WEB_SRC / 'api' / 'nutrition.ts'
    search_call = {"found_in_code": False, "url": None}
    add_item_call = {"found_in_code": False, "url": None}
    search_log = []
    add_item_log = []
    if api_nutrition.exists():
        s_hits = grep_with_lines(re.compile(r"/nutrition/foods/search"), api_nutrition)
        a_hits = grep_with_lines(re.compile(r"/nutrition/meal/.+/items"), api_nutrition)
        if s_hits:
            search_call["found_in_code"] = True
            search_log = s_hits
        if a_hits:
            add_item_call["found_in_code"] = True
            add_item_log = a_hits

    # 3b) Base URL
    env_local = ROOT / 'web' / '.env.local'
    base_url = None
    if env_local.exists():
        m = re.search(r"^VITE_API_BASE_URL=(.*)$", read_text_safe(env_local), re.M)
        if m:
            base_url = m.group(1).strip()
    # path-only URL reporting
    def to_path(url: str) -> str:
        try:
            # naive parse to grab pathname
            m = re.match(r"^[a-z]+://[^/]+(?P<path>/.*)$", url)
            return m.group('path') if m else url
        except Exception:
            return url

    search_url = (to_path(base_url + '/nutrition/foods/search') if base_url else '/api/v1/nutrition/foods/search')
    add_item_url = (to_path(base_url + '/nutrition/meal/{meal_id}/items') if base_url else '/api/v1/nutrition/meal/{meal_id}/items')
    search_call["url"] = search_url
    add_item_call["url"] = add_item_url

    # 4) Debounce
    debounce_ms = None
    if component_found:
        txt = read_text_safe(food_picker)
        m = re.search(r"useDebouncedValue\([^,]+,\s*(\d+)\)", txt)
        if m:
            debounce_ms = int(m.group(1))
    if debounce_ms is None:
        hook = WEB_SRC / 'hooks' / 'useDebouncedValue.ts'
        if hook.exists():
            m = re.search(r"export function useDebouncedValue<.*?>\([^,]+,\s*(\d+)\)", read_text_safe(hook))
            if m:
                debounce_ms = int(m.group(1))

    # 5) UI states & manual fallback
    ui_states = {"loading": False, "empty": False, "error": False, "manual_fallback": False}
    ui_evidence = []
    if component_found:
        for i, line in enumerate(read_text_safe(food_picker).splitlines(), 1):
            if 'Buscando' in line:
                ui_states["loading"] = True
                ui_evidence.append({"file": str(food_picker), "line": i, "text": line.strip()})
            if 'Sin resultados' in line:
                ui_states["empty"] = True
                ui_evidence.append({"file": str(food_picker), "line": i, "text": line.strip()})
            if 'error de búsqueda' in line:
                ui_states["error"] = True
                ui_evidence.append({"file": str(food_picker), "line": i, "text": line.strip()})
            if 'Entrada manual' in line:
                ui_states["manual_fallback"] = True
                ui_evidence.append({"file": str(food_picker), "line": i, "text": line.strip()})

    report = {
        "frontend_audit": {
            "component_found": "FoodPicker" if component_found else None,
            "wired_in_meals": wired_in_meals,
            "api_calls": {
                "search": search_call,
                "add_item": add_item_call,
            },
            "devtools_network": {
                "search_typing_manzana": {"requests": 0, "status": [], "debounce_ms": debounce_ms},
            },
            "fallback_manual_entry": 'PASS' if ui_states.get('manual_fallback') else 'FAIL',
            "notes": [],
        }
    }

    if not component_found:
        report["frontend_audit"]["notes"].append("Autocomplete component not found")
    if debounce_ms is not None and debounce_ms < 250:
        report["frontend_audit"]["notes"].append(f"Debounce too low: {debounce_ms}ms")
    if debounce_ms is not None and debounce_ms >= 250:
        report["frontend_audit"]["notes"].append(f"Debounce OK: {debounce_ms}ms")
    if not ui_states.get('loading'):
        report["frontend_audit"]["notes"].append("Loading state not detected")
    if not ui_states.get('error'):
        report["frontend_audit"]["notes"].append("Error state not detected")
    if not ui_states.get('empty'):
        report["frontend_audit"]["notes"].append("Empty state not detected")

    log = {
        "files_scanned": len(all_src_files),
        "component": {"path": str(food_picker) if component_found else None, "found": component_found},
        "meals_today": {"path": str(meals_today), "imports": meals_imports},
        "api_client": {"path": str(WEB_SRC / 'api' / 'client.ts'), "base_env_key": 'VITE_API_BASE_URL'},
        "api_routes": {
            "search": search_log,
            "add_item": add_item_log,
        },
        "ui_evidence": ui_evidence,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\n--- audit log ---")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
