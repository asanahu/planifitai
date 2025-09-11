import { apiFetch } from './client';

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'other';
export type ServingUnit = 'g' | 'ml' | 'unit';

export interface MealItem {
  id: number;
  food_name: string | null;
  serving_qty: number;
  serving_unit: ServingUnit;
  calories_kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface Meal {
  id: number;
  date: string;
  meal_type: MealType;
  name?: string | null;
  items: MealItem[];
}

export interface DayLog {
  date: string;
  meals: Meal[];
  totals: { calories_kcal: number; protein_g: number; carbs_g: number; fat_g: number };
  water_total_ml: number;
  targets?: { calories_target: number } | null;
  adherence?: { calories?: number } | null; // 0..1
}

export interface Summary {
  start: string;
  end: string;
  days: number;
  totals: { calories_kcal: number };
  adherence?: { calories?: number } | null;
}

export function getDayLog(date: string) {
  return apiFetch<DayLog>(`/nutrition?date=${date}`);
}

export function createMeal(payload: { date: string; meal_type: MealType; name?: string }) {
  return apiFetch(`/nutrition/meal`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateMeal(id: number, payload: Partial<{ meal_type: MealType; name: string; notes: string }>) {
  return apiFetch(`/nutrition/meal/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function deleteMeal(id: number) {
  return apiFetch(`/nutrition/meal/${id}`, { method: 'DELETE' });
}

export type AddMealItemFlexible =
  | {
      food_id: string;
      quantity: number;
      unit: 'g' | 'ml' | 'unidad';
    }
  | {
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

export function addMealItemFlexible(mealId: number | string, payload: AddMealItemFlexible) {
  const body = 'serving_unit' in (payload as any) && (payload as any).serving_unit === 'unidad'
    ? { ...(payload as any), serving_unit: 'unit' }
    : payload;
  return apiFetch(`/nutrition/meal/${mealId}/items`, { method: 'POST', body: JSON.stringify(body) });
}

export function updateMealItem(mealId: number, itemId: number, payload: Partial<{ serving_qty: number; serving_unit: ServingUnit; calories_kcal: number; protein_g: number; carbs_g: number; fat_g: number }>) {
  return apiFetch(`/nutrition/meal/${mealId}/items/${itemId}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function deleteMealItem(mealId: number, itemId: number) {
  return apiFetch(`/nutrition/meal/${mealId}/items/${itemId}`, { method: 'DELETE' });
}

export function getTargets(date: string) {
  return apiFetch<{ date: string; calories_target: number }>(`/nutrition/targets?date=${date}`);
}

export function getSummary(start: string, end: string) {
  return apiFetch<Summary>(`/nutrition/summary?start=${start}&end=${end}`);
}

export function addWater(volume_ml: number) {
  return apiFetch('/nutrition/water', {
    method: 'POST',
    body: JSON.stringify({ datetime_utc: new Date().toISOString(), volume_ml }),
  });
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
// (moved flexible add above)
