import { apiFetch } from './client';

export interface Exercise {
  id: string;
  name: string;
  completed: boolean;
  catalog_id?: string | number;
  sets?: number;
  reps?: number;
  time_seconds?: number;
  rest_seconds?: number;
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
    name?: string;
    duration?: number;
    equipment?: string[];
    exercises: { name: string; reps?: number; sets?: number; time?: number }[];
  }[];
}

function computeDateFromWeekday(weekday: number): string {
  const now = new Date();
  // Compute Monday of current week
  const day = now.getDay(); // 0=Sun..6=Sat
  const mondayOffset = (day + 6) % 7; // days since Monday
  const monday = new Date(now);
  monday.setHours(0, 0, 0, 0);
  monday.setDate(now.getDate() - mondayOffset);
  const d = new Date(monday);
  d.setDate(monday.getDate() + weekday);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
}

function adaptRoutine(r: any): Routine {
  return {
    id: String(r.id),
    name: r.name,
    days: (r.days || []).map((d: any) => ({
      id: String(d.id),
      date: d.date || computeDateFromWeekday(typeof d.weekday === 'number' ? d.weekday : 0),
      exercises: (d.exercises || []).map((e: any) => ({
        id: String(e.id),
        name: e.exercise_name || e.name || 'Exercise',
        completed: !!e.completed,
        catalog_id: e.exercise_id,
        sets: e.sets,
        reps: e.reps,
        time_seconds: e.time_seconds,
        rest_seconds: e.rest_seconds,
      })),
    })),
  };
}

export async function listRoutines() {
  const server = await apiFetch<any[]>('/routines');
  return server.map(adaptRoutine);
}

export function getUserRoutines() {
  return listRoutines();
}

export async function getRoutine(id: string) {
  const r = await apiFetch<any>(`/routines/${id}`);
  return adaptRoutine(r);
}

export async function getPlannedDayFor(date: Date) {
  const routines = await getUserRoutines();
  const target = date.toISOString().slice(0, 10);
  for (const routine of routines) {
    const day = routine.days.find((d) => d.date === target);
    if (day) {
      // Compute next upcoming session within the current week
      const future = routine.days
        .map((d) => d.date)
        .filter((d) => d > target)
        .sort();
      const next = future[0];
      return { routine, day, next, isFallback: false } as any;
    }
  }
  // Fallback: return the latest routine with its first day so Today can show progress/adherence
  if (routines.length > 0) {
    const routine = routines[routines.length - 1];
    // Determine next session: first day in the future this week, otherwise the earliest day next week
    const days = routine.days.map((d) => d.date).sort();
    const future = days.filter((d) => d > target);
    let next = future[0] || days[0] || undefined;
    // If next is in the past (no future days), we consider it next week (add +7d when presenting)
    return { routine, day: undefined, next, isFallback: true } as any;
  }
  return null;
}

export function completeExercise(routineId: string, dayId: string, exerciseId: string, dayDate?: string) {
  const ts = dayDate ? `${dayDate}T00:00:00Z` : new Date().toISOString();
  const body = JSON.stringify({ timestamp: ts });
  return apiFetch(`/routines/${routineId}/days/${dayId}/exercises/${exerciseId}/complete`, {
    method: 'POST',
    body,
  });
}

export function completeDay(routineId: string, dayId: string, dayDate?: string) {
  const body = dayDate ? JSON.stringify({ timestamp: `${dayDate}T00:00:00Z` }) : undefined;
  return apiFetch(`/routines/${routineId}/days/${dayId}/complete`, { method: 'POST', body });
}

export function uncompleteDay(routineId: string, dayId: string, dayDate?: string) {
  const opts: RequestInit = { method: 'POST' };
  if (dayDate) {
    opts.body = JSON.stringify({ date: dayDate });
  }
  return apiFetch(`/routines/${routineId}/days/${dayId}/uncomplete`, opts);
}

export function uncompleteExercise(routineId: string, dayId: string, exerciseId: string, dayDate?: string) {
  const body = JSON.stringify({ timestamp: dayDate ? `${dayDate}T00:00:00Z` : new Date().toISOString() });
  return apiFetch(`/routines/${routineId}/days/${dayId}/exercises/${exerciseId}/uncomplete`, {
    method: 'POST',
    body,
  });
}

export function createRoutine(payload: RoutineCreatePayload) {
  // Adapt payload to backend schema (RoutineCreate -> RoutineDayCreate -> RoutineExerciseCreate)
  const adapted = {
    name: payload.name,
    days: payload.days.map((d, i) => ({
      weekday: d.weekday,
      order_index: i,
      equipment: d.equipment,
      exercises: d.exercises.map((ex, j) => ({
        exercise_name: ex.name,
        sets: ex.sets ?? 3,
        reps: ex.reps,
        time_seconds: ex.time,
        order_index: j,
      })),
    })),
  };
  return apiFetch<Routine>('/routines', {
    method: 'POST',
    body: JSON.stringify(adapted),
  });
}

// No-op: backend no tiene endpoint de "activar" rutina; mantenemos compatibilidad
export function setActiveRoutine(_id: string) {
  return Promise.resolve(undefined as any);
}

export function cloneTemplate(templateId: string) {
  return apiFetch<Routine>(`/routines/templates/${templateId}/clone`, { method: 'POST' });
}

export function updateRoutineDay(
  routineId: string | number,
  dayId: string | number,
  payload: Partial<{ equipment: string[]; weekday: number; order_index: number }>
) {
  return apiFetch<RoutineDay>(`/routines/${routineId}/days/${dayId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function addExerciseToDay(
  routineId: string | number,
  dayId: string | number,
  exercise: { exercise_name: string; exercise_id?: string | number; sets?: number; reps?: number; time_seconds?: number; rest_seconds?: number; notes?: string }
) {
  const body = JSON.stringify({
    exercise_name: exercise.exercise_name,
    exercise_id: exercise.exercise_id,
    sets: exercise.sets ?? 3,
    reps: exercise.reps,
    time_seconds: exercise.time_seconds,
    rest_seconds: exercise.rest_seconds,
    notes: exercise.notes,
  });
  return apiFetch(`/routines/${routineId}/days/${dayId}/exercises`, { method: 'POST', body });
}
