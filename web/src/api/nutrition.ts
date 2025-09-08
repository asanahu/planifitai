import { apiFetch } from './client';

export interface MealItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  calories: number;
}

export interface Meal {
  id: string;
  name: string;
  items: MealItem[];
}

export interface DayLog {
  date: string;
  meals: Meal[];
  targets: { calories: number };
  totals: { calories: number };
  adherence?: { calories: number };
  calories?: number;
}

export interface Targets {
  calories: number;
}

export interface Summary {
  date: string;
  calories: number;
  target?: number;
}

export interface MealPlanCreatePayload {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

export function getDayLog(date: string) {
  return apiFetch<DayLog>(`/nutrition?date=${date}`);
}

export function createMeal(date: string, payload: { name: string }) {
  return apiFetch(`/nutrition/meal?date=${date}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateMeal(id: string, payload: { name: string }) {
  return apiFetch(`/nutrition/meal/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function deleteMeal(id: string) {
  return apiFetch(`/nutrition/meal/${id}`, { method: 'DELETE' });
}

export function createMealItem(mealId: string, payload: { name: string; quantity: number; unit: string; calories: number }) {
  return apiFetch(`/nutrition/meal/${mealId}/items`, { method: 'POST', body: JSON.stringify(payload) });
}

export function updateMealItem(id: string, payload: Partial<{ name: string; quantity: number; unit: string; calories: number }>) {
  return apiFetch(`/nutrition/meal-items/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function deleteMealItem(id: string) {
  return apiFetch(`/nutrition/meal-items/${id}`, { method: 'DELETE' });
}

export function getTargets(date: string) {
  return apiFetch<Targets>(`/nutrition/targets?date=${date}`);
}

export function getSummary(start: string, end: string) {
  return apiFetch<Summary[]>(`/nutrition/summary?start=${start}&end=${end}`);
}

export function addWater(amount: number) {
  return apiFetch('/nutrition/water', {
    method: 'POST',
    body: JSON.stringify({ amount }),
  });
}

export function createMealPlan(payload: MealPlanCreatePayload) {
  return apiFetch('/meal-plans', { method: 'POST', body: JSON.stringify(payload) });
}

export function getMealPlan(params: { start: string; end: string }) {
  return apiFetch(`/meal-plans?start=${params.start}&end=${params.end}`);
}

// --- Food search/cache (frontend)

export interface FoodHit {
  id: string;
  name: string;
  brand?: string | null;
  calories_kcal?: number | null;
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
}

export interface FoodDetails extends FoodHit {
  source: string;
  source_id: string;
  portion_suggestions?: Record<string, unknown> | null;
}

export function searchFoods(q: string, page = 1, pageSize = 10) {
  const qs = new URLSearchParams({ q, page: String(page), page_size: String(pageSize) });
  return apiFetch<FoodHit[]>(`/nutrition/foods/search?${qs.toString()}`);
}

export function getFoodDetails(foodId: string) {
  return apiFetch<FoodDetails>(`/nutrition/foods/${foodId}`);
}

// Flexible item creation: food-driven or manual payloads
export type AddMealItemFlexible =
  | {
      food_id: string;
      quantity: number;
      unit: 'g' | 'ml' | 'unidad';
    }
  | {
      // manual legacy-compatible shape
      food_name: string;
      serving_qty: number;
      serving_unit: 'g' | 'ml' | 'unit' | 'unidad';
      calories_kcal: number;
      protein_g: number;
      carbs_g: number;
      fat_g: number;
      fiber_g?: number;
      sugar_g?: number;
      sodium_mg?: number;
    };

export function addMealItemFlexible(mealId: string, payload: AddMealItemFlexible) {
  // normalize unidad -> unit for manual serving_unit if needed
  const body = 'serving_unit' in payload && payload.serving_unit === 'unidad'
    ? { ...payload, serving_unit: 'unit' }
    : payload;
  return apiFetch(`/nutrition/meal/${mealId}/items`, { method: 'POST', body: JSON.stringify(body) });
}
