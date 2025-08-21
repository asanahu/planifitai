import { apiFetch } from './client';

export interface Exercise {
  id: string;
  name: string;
  completed: boolean;
}

export interface RoutineDay {
  id: string;
  date: string;
  exercises: Exercise[];
}

export interface Routine {
  id: string;
  name: string;
  days: RoutineDay[];
}

export function listRoutines() {
  return apiFetch<Routine[]>('/routines');
}

export function getRoutine(id: string) {
  return apiFetch<Routine>(`/routines/${id}`);
}

export function completeExercise(routineId: string, dayId: string, exerciseId: string) {
  return apiFetch(`/routines/${routineId}/days/${dayId}/exercises/${exerciseId}/complete`, {
    method: 'POST',
  });
}
