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
    equipment_by_day: Record<number, string[]>;
    preferences: Record<string, string>;
    preferred_days: number[]; // 0=Lunes..6=Domingo
    injuries: string[];
  }> = {}
) {
  const simulate = (import.meta.env.VITE_AI_SIMULATE as string | undefined) === '1';
  const timeoutMs = Number((import.meta.env.VITE_AI_TIMEOUT_MS as string | undefined) ?? '35000');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort('timeout'), Math.max(1000, timeoutMs));
  const body = {
    days_per_week: payload.days_per_week ?? payload.days ?? 3,
    equipment: payload.equipment,
    equipment_by_day: payload.equipment_by_day,
    preferences: payload.preferences,
    preferred_days: payload.preferred_days,
    injuries: payload.injuries,
  };
  const path = `/ai/generate/workout-plan${simulate ? '?simulate=1' : ''}`;
  return apiFetch<AiWorkoutPlanJSON>(path, {
    method: 'POST',
    body: JSON.stringify(body),
    signal: controller.signal,
  }).finally(() => clearTimeout(timer));
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
  const simulate = (import.meta.env.VITE_AI_SIMULATE as string | undefined) === '1';
  const timeoutMs = Number((import.meta.env.VITE_AI_TIMEOUT_MS as string | undefined) ?? '60000'); // Reducido a 1 minuto
  const controller = new AbortController();
  const timer = setTimeout(() => {
    console.log('⏰ Timeout alcanzado, cancelando petición...');
    controller.abort('timeout');
  }, Math.max(1000, timeoutMs));
  
  const prefs = payload.preferences || (payload.prefs ? { prefs: payload.prefs.join(', ') } : undefined);
  const body = {
    days: payload.days ?? 7,
    preferences: prefs,
  };
  const path = `/ai/generate/nutrition-plan${simulate ? '?simulate=1' : ''}`;
  
  console.log('🔧 generateNutritionPlanAI config:', {
    simulate,
    timeoutMs,
    body,
    path,
    useAbortController: true
  });
  
  return apiFetch<AiNutritionPlanJSON>(path, {
    method: 'POST',
    body: JSON.stringify(body),
    signal: controller.signal,
  }).finally(() => {
    clearTimeout(timer);
    console.log('🧹 Timer limpiado');
  });
}

// --- Smart Food Search -----------------------------------------------------

export interface SmartFoodSearchRequest {
  query: string;
  context?: string;
  max_suggestions?: number;
}

export interface SmartFoodSearchResponse {
  enhanced_query: string;
  search_terms: string[];
  suggestions: string[];
  context_notes?: string;
}

export function enhanceFoodSearch(payload: SmartFoodSearchRequest, simulate = false) {
  const qs = new URLSearchParams({ simulate: String(simulate) });
  return apiFetch<SmartFoodSearchResponse>(`/ai/food-search/enhance?${qs.toString()}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getFoodSuggestions(query: string, context?: string, simulate = false) {
  const qs = new URLSearchParams({ 
    query, 
    ...(context && { context }),
    simulate: String(simulate)
  });
  return apiFetch<{ suggestions: string[] }>(`/ai/food-search/suggestions?${qs.toString()}`);
}

export function getEnhancedSearchTerms(query: string, context?: string, simulate = false) {
  const qs = new URLSearchParams({ 
    query, 
    ...(context && { context }),
    simulate: String(simulate)
  });
  return apiFetch<{ search_terms: string[] }>(`/ai/food-search/terms?${qs.toString()}`);
}

