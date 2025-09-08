#!/usr/bin/env node
/**
 * Frontend audit for food autocomplete integration.
 * - Performs static code search for component wiring and API routes.
 * - (Optional) Could run a headless browser to capture real requests.
 *
 * Usage: node scripts/verify_food_frontend.mjs
 */

import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const WEB_SRC = path.join(ROOT, 'web', 'src');

function read(file) {
  return readFileSync(file, 'utf8');
}

function walk(dir) {
  const out = [];
  const entries = readdirSync(dir);
  for (const e of entries) {
    const p = path.join(dir, e);
    const st = statSync(p);
    if (st.isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out;
}

function findFilesMatching(re, files) {
  const hits = [];
  for (const f of files) {
    try {
      const txt = read(f);
      if (re.test(txt)) hits.push(f);
    } catch {
      // ignore
    }
  }
  return hits;
}

function grepWithLines(pattern, file) {
  const txt = read(file);
  const lines = txt.split(/\r?\n/);
  const re = typeof pattern === 'string' ? new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) : pattern;
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    if (re.test(lines[i])) out.push({ line: i + 1, text: lines[i].trim() });
  }
  return out;
}

function pathIfExists(p) {
  try {
    statSync(p);
    return p;
  } catch {
    return null;
  }
}

// Collect files
const allSrcFiles = walk(WEB_SRC).filter((p) => /\.(ts|tsx|js|jsx|mjs)$/i.test(p));

// 1) Locate autocomplete component
const foodPickerPath = pathIfExists(path.join(WEB_SRC, 'components', 'FoodPicker.tsx'));
const componentFound = !!foodPickerPath;

// 2) Verify Meals screen wiring (MealsToday uses FoodPicker)
const mealsTodayPath = pathIfExists(path.join(WEB_SRC, 'features', 'nutrition', 'MealsToday.tsx'));
let wiredInMeals = 'FAIL';
let mealsTodayImports = [];
if (mealsTodayPath) {
  mealsTodayImports = grepWithLines(/FoodPicker/, mealsTodayPath);
  if (mealsTodayImports.length > 0) wiredInMeals = 'PASS';
}

// 3) Search for API calls
const apiNutritionPath = pathIfExists(path.join(WEB_SRC, 'api', 'nutrition.ts'));
const apiClientPath = pathIfExists(path.join(WEB_SRC, 'api', 'client.ts'));

let searchCall = { found_in_code: false, url: null };
let addItemCall = { found_in_code: false, url: null };
let searchLog = [];
let addItemLog = [];

if (apiNutritionPath) {
  const searchLines = grepWithLines(/\/nutrition\/foods\/search/, apiNutritionPath);
  const addItemLines = grepWithLines(/\/nutrition\/meal\/.+\/items/, apiNutritionPath);
  if (searchLines.length) {
    searchCall.found_in_code = true;
    searchCall.url = '/nutrition/foods/search';
    searchLog = searchLines.map((l) => ({ file: apiNutritionPath, ...l }));
  }
  if (addItemLines.length) {
    addItemCall.found_in_code = true;
    addItemCall.url = '/nutrition/meal/{meal_id}/items';
    addItemLog = addItemLines.map((l) => ({ file: apiNutritionPath, ...l }));
  }
}

// 3b) Resolve base URL from API client
let baseUrl = null;
let baseUrlKey = null;
if (apiClientPath) {
  const clientText = read(apiClientPath);
  const m = clientText.match(/VITE_API_BASE_URL/);
  if (m) baseUrlKey = 'VITE_API_BASE_URL';
  const demoMatch = clientText.match(/const\s+DEMO_MODE\s*=\s*import\.meta\.env\.VITE_DEMO\s*===\s*'1'/);
  const apiMatch = clientText.match(/const\s+API_URL\s*=\s*DEMO_MODE\s*\?\s*''\s*:\s*import\.meta\.env\.VITE_API_BASE_URL/);
  if (apiMatch) baseUrl = '<env:VITE_API_BASE_URL>';
}

// 4) Debounce check inside FoodPicker/hook
let debounceMs = null;
let debounceEvidence = [];
const debounceHookPath = pathIfExists(path.join(WEB_SRC, 'hooks', 'useDebouncedValue.ts'));
if (foodPickerPath) {
  const fpText = read(foodPickerPath);
  const m = fpText.match(/useDebouncedValue\([^,]+,\s*(\d+)\)/);
  if (m) {
    debounceMs = Number(m[1]);
    debounceEvidence.push({ file: foodPickerPath, line: grepWithLines(/useDebouncedValue\(/, foodPickerPath)[0]?.line ?? null });
  }
}
if (!debounceMs && debounceHookPath) {
  const hookText = read(debounceHookPath);
  const m = hookText.match(/export function useDebouncedValue<[^>]*>\([^,]+,\s*(\d+)\)\s*\{/);
  if (m) debounceMs = Number(m[1]);
}

// 5) UI state checks in FoodPicker
let uiStates = { loading: false, empty: false, error: false, manual_fallback: false };
let uiEvidence = [];
if (foodPickerPath) {
  const lines = read(foodPickerPath).split(/\r?\n/);
  lines.forEach((line, idx) => {
    if (/Buscando/.test(line)) { uiStates.loading = true; uiEvidence.push({ file: foodPickerPath, line: idx + 1, text: line.trim() }); }
    if (/Sin resultados\)/.test(line)) { uiStates.empty = true; uiEvidence.push({ file: foodPickerPath, line: idx + 1, text: line.trim() }); }
    if (/error de búsqueda/.test(line)) { uiStates.error = true; uiEvidence.push({ file: foodPickerPath, line: idx + 1, text: line.trim() }); }
    if (/Entrada manual/.test(line)) { uiStates.manual_fallback = true; uiEvidence.push({ file: foodPickerPath, line: idx + 1, text: line.trim() }); }
  });
}

// 6) Compose final JSON
const apiBasePrefix = baseUrl === '<env:VITE_API_BASE_URL>' ? '/api/v1' : '';
// Try to read web/.env.local to refine prefix
try {
  const envLocal = read(path.join(ROOT, 'web', '.env.local'));
  const m = envLocal.match(/^VITE_API_BASE_URL=(.*)$/m);
  if (m) {
    const url = m[1].trim();
    const u = new URL(url);
    // take pathname part as prefix
    if (u.pathname && u.pathname !== '/') {
      // normalize to no trailing slash
      const pfx = u.pathname.endsWith('/') ? u.pathname.slice(0, -1) : u.pathname;
      // ex: /api/v1
      baseUrl = url;
      // override prefix used in reported URLs
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const _ = apiBasePrefix; // to show intent
    }
  }
} catch {}

const searchUrl = baseUrl ? new URL('/nutrition/foods/search', baseUrl).pathname : '/api/v1/nutrition/foods/search';
const addItemUrl = baseUrl ? new URL('/nutrition/meal/{meal_id}/items', baseUrl).pathname : '/api/v1/nutrition/meal/{meal_id}/items';

const report = {
  frontend_audit: {
    component_found: componentFound ? 'FoodPicker' : null,
    wired_in_meals: wiredInMeals,
    api_calls: {
      search: { found_in_code: searchCall.found_in_code, url: searchUrl },
      add_item: { found_in_code: addItemCall.found_in_code, url: addItemUrl },
    },
    devtools_network: {
      search_typing_manzana: { requests: 0, status: [], debounce_ms: debounceMs ?? null },
    },
    fallback_manual_entry: uiStates.manual_fallback ? 'PASS' : 'FAIL',
    notes: [],
  },
};

// Compute PASS/FAIL notes
if (!componentFound) report.frontend_audit.notes.push('Autocomplete component not found');
if (debounceMs && debounceMs < 250) report.frontend_audit.notes.push(`Debounce too low: ${debounceMs}ms`);
if (debounceMs && debounceMs >= 250) report.frontend_audit.notes.push(`Debounce OK: ${debounceMs}ms`);
if (!uiStates.loading) report.frontend_audit.notes.push('Loading state not detected');
if (!uiStates.error) report.frontend_audit.notes.push('Error state not detected');
if (!uiStates.empty) report.frontend_audit.notes.push('Empty state not detected');

// Build log
const log = {
  files_scanned: allSrcFiles.length,
  component: { path: foodPickerPath, found: componentFound },
  meals_today: { path: mealsTodayPath, imports: mealsTodayImports },
  api_client: { path: apiClientPath, base_env_key: baseUrlKey },
  api_routes: {
    search: searchLog,
    add_item: addItemLog,
  },
  ui_evidence: uiEvidence,
};

// Output
console.log(JSON.stringify(report, null, 2));
console.log('\n--- audit log ---');
console.log(JSON.stringify(log, null, 2));

