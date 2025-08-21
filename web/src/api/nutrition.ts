import { apiFetch } from './client';

export interface MealItem {
  id: string;
  name: string;
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
  water: number;
  targets: { calories: number };
  calories: number;
}

export function getDayLog(date: string) {
  return apiFetch<DayLog>(`/nutrition?date=${date}`);
}

export function addMeal(data: { name: string; items: MealItem[] }) {
  return apiFetch('/nutrition/meal', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function addWater(amount: number) {
  return apiFetch('/nutrition/water', {
    method: 'POST',
    body: JSON.stringify({ amount }),
  });
}
