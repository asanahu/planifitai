export interface MealPlan {
  [day: string]: {
    [meal: string]: string[];
  };
}

export interface MealActuals {
  [day: string]: {
    [meal: string]: string[];
  };
}

const KEY = 'mealPlan:v1';
const KEY_ACTUALS = 'mealActuals:v1';

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

export function getMealActuals(): MealActuals {
  try {
    const raw = localStorage.getItem(KEY_ACTUALS);
    return raw ? (JSON.parse(raw) as MealActuals) : {};
  } catch {
    return {} as MealActuals;
  }
}

export function setMealActuals(actuals: MealActuals) {
  localStorage.setItem(KEY_ACTUALS, JSON.stringify(actuals));
}

export function clearMealActuals() {
  localStorage.removeItem(KEY_ACTUALS);
}
