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

// Nuevo sistema de almacenamiento por semanas
export interface WeeklyMealPlan {
  [weekKey: string]: MealPlan;
}

export interface WeeklyMealActuals {
  [weekKey: string]: MealActuals;
}

const KEY = 'mealPlan:v1';
const KEY_ACTUALS = 'mealActuals:v1';
const KEY_WEEKLY_PLAN = 'weeklyMealPlan:v2';
const KEY_WEEKLY_ACTUALS = 'weeklyMealActuals:v2';

// Funciones legacy (mantener para compatibilidad)
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

// Nuevas funciones para almacenamiento por semanas
export function getWeeklyMealPlan(): WeeklyMealPlan {
  try {
    const raw = localStorage.getItem(KEY_WEEKLY_PLAN);
    return raw ? (JSON.parse(raw) as WeeklyMealPlan) : {};
  } catch {
    return {} as WeeklyMealPlan;
  }
}

export function setWeeklyMealPlan(weeklyPlan: WeeklyMealPlan) {
  localStorage.setItem(KEY_WEEKLY_PLAN, JSON.stringify(weeklyPlan));
}

export function getWeeklyMealActuals(): WeeklyMealActuals {
  try {
    const raw = localStorage.getItem(KEY_WEEKLY_ACTUALS);
    return raw ? (JSON.parse(raw) as WeeklyMealActuals) : {};
  } catch {
    return {} as WeeklyMealActuals;
  }
}

export function setWeeklyMealActuals(weeklyActuals: WeeklyMealActuals) {
  localStorage.setItem(KEY_WEEKLY_ACTUALS, JSON.stringify(weeklyActuals));
}

// Funciones de utilidad para trabajar con semanas específicas
export function getMealPlanForWeek(weekKey: string): MealPlan {
  const weeklyPlan = getWeeklyMealPlan();
  return weeklyPlan[weekKey] || {};
}

export function setMealPlanForWeek(weekKey: string, plan: MealPlan) {
  const weeklyPlan = getWeeklyMealPlan();
  weeklyPlan[weekKey] = plan;
  setWeeklyMealPlan(weeklyPlan);
}

export function getMealActualsForWeek(weekKey: string): MealActuals {
  const weeklyActuals = getWeeklyMealActuals();
  return weeklyActuals[weekKey] || {};
}

export function setMealActualsForWeek(weekKey: string, actuals: MealActuals) {
  const weeklyActuals = getWeeklyMealActuals();
  weeklyActuals[weekKey] = actuals;
  setWeeklyMealActuals(weeklyActuals);
}

export function clearWeeklyMealPlan() {
  localStorage.removeItem(KEY_WEEKLY_PLAN);
}

export function clearWeeklyMealActuals() {
  localStorage.removeItem(KEY_WEEKLY_ACTUALS);
}
