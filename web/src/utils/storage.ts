export interface MealPlan {
  [day: string]: {
    [meal: string]: string[];
  };
}

const KEY = 'mealPlan:v1';

export function getMealPlan(): MealPlan {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as MealPlan) : {};
  } catch {
    return {} as MealPlan;
  }
}

export function setMealPlan(plan: MealPlan) {
  localStorage.setItem(KEY, JSON.stringify(plan));
}

export function clearMealPlan() {
  localStorage.removeItem(KEY);
}
