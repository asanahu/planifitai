import { apiFetch } from './client';

export interface AiWorkoutPlanJSON {
  // Backend shape (schemas.WorkoutPlan)
  name?: string;
  days_per_week?: number;
  days?: { weekday?: string; focus?: string; exercises?: { name?: string; reps?: number; sets?: number; rest_sec?: number; notes?: string }[] }[];
}

export interface AiNutritionPlanJSON {
  // Backend shape (schemas.NutritionPlan)
  days?: { date?: string; meals?: { type?: string; items?: any[]; meal_kcal?: number }[]; totals?: Record<string, number> }[];
  targets?: Record<string, number>;
}

// Accept legacy payload from UI but map to backend schema
export function generateWorkoutPlanAI(
  payload: Partial<{
    // legacy
    goal: string;
    level: string;
    days: number;
    // backend
    days_per_week: number;
    equipment: string;
    preferences: Record<string, string>;
  }> = {}
) {
  const body = {
    days_per_week: payload.days_per_week ?? payload.days ?? 3,
    equipment: payload.equipment,
    preferences: payload.preferences,
  };
  return apiFetch<AiWorkoutPlanJSON>('/ai/generate/workout-plan', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function generateNutritionPlanAI(
  payload: Partial<{
    // legacy
    calories: number;
    prefs: string[];
    // backend
    days: number;
    preferences: Record<string, string>;
  }> = {}
) {
  const prefs = payload.preferences || (payload.prefs ? { prefs: payload.prefs.join(', ') } : undefined);
  const body = {
    days: payload.days ?? 7,
    preferences: prefs,
  };
  return apiFetch<AiNutritionPlanJSON>('/ai/generate/nutrition-plan', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

