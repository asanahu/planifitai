import { apiFetch } from './client';

export interface AiWorkoutPlanJSON {
  name?: string;
  days?: { name?: string; exercises?: { name?: string; reps?: number; sets?: number; duration?: number }[] }[];
}

export interface AiNutritionPlanJSON {
  days?: { day?: string; meals?: { name?: string; items?: string[] }[] }[];
}

export function generateWorkoutPlanAI(payload: Partial<{ goal: string; level: string; days: number }> = {}) {
  return apiFetch<AiWorkoutPlanJSON>('/ai/generate/workout-plan', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function generateNutritionPlanAI(payload: Partial<{ calories: number; prefs: string[] }> = {}) {
  return apiFetch<AiNutritionPlanJSON>('/ai/generate/nutrition-plan', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

