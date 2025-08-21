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

export function getUserRoutines() {
  return listRoutines();
}

export function getRoutine(id: string) {
  return apiFetch<Routine>(`/routines/${id}`);
}

export async function getPlannedDayFor(date: Date) {
  const routines = await getUserRoutines();
  const target = date.toISOString().slice(0, 10);
  for (const routine of routines) {
    const day = routine.days.find((d) => d.date === target);
    if (day) {
      return { routine, day };
    }
  }
  return null;
}

export function completeExercise(routineId: string, dayId: string, exerciseId: string) {
  return apiFetch(`/routines/${routineId}/days/${dayId}/exercises/${exerciseId}/complete`, {
    method: 'POST',
  });
}

export function completeDay(routineId: string, dayId: string) {
  return apiFetch(`/routines/${routineId}/days/${dayId}/complete`, { method: 'POST' });
}

export async function createRoutineFromAI() {
  const plan = await apiFetch<unknown>('/ai/generate/workout-plan', { method: 'POST' });
  return apiFetch<Routine>('/routines', {
    method: 'POST',
    body: JSON.stringify(plan),
  });
}
