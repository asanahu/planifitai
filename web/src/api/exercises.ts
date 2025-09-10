import { apiFetch } from './client';

export interface ExerciseItem {
  id: number | string;
  name: string;
  muscle_groups: string[];
  equipment?: string | null;
  level?: string | null;
  demo_url?: string | null;
}

export interface ExerciseCatalogResponse {
  items: ExerciseItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ExerciseCatalogParams {
  q?: string;
  muscle?: string;
  equipment?: string;
  level?: string;
  limit?: number;
  offset?: number;
}

export function getExerciseCatalog(params: ExerciseCatalogParams = {}) {
  const qs = new URLSearchParams();
  if (params.q) qs.set('q', params.q);
  if (params.muscle) qs.set('muscle', params.muscle);
  if (params.equipment) qs.set('equipment', params.equipment);
  if (params.level) qs.set('level', params.level);
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.offset) qs.set('offset', String(params.offset));
  const query = qs.toString();
  return apiFetch<ExerciseCatalogResponse>(`/routines/exercise-catalog${query ? `?${query}` : ''}`);
}

export function getExerciseFilters() {
  return apiFetch<{ equipment: string[]; muscles: string[] }>(`/routines/exercise-filters`);
}
