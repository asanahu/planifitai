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

export interface RoutineCreatePayload {
  name: string;
  days: {
    weekday: number;
    name: string;
    duration: number;
    exercises: { name: string; reps: number; time: number }[];
  }[];
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

export function createRoutine(payload: RoutineCreatePayload) {
  return apiFetch<Routine>('/routines', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function setActiveRoutine(id: string) {
  return apiFetch(`/routines/${id}`, { method: 'PATCH', body: JSON.stringify({ active: true }) });
}
