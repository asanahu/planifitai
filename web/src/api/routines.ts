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
  start_date?: string;
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

function pad(n: number): string { return String(n).padStart(2, '0'); }

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
  const m = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  return `${y}-${m}-${dd}`;
}

function computeDateFromStart(startDateISO?: string, weekday?: number): string | undefined {
  if (!startDateISO || typeof weekday !== 'number') return undefined;
  const baseStr = startDateISO.slice(0, 10);
  const [y, m, d] = baseStr.split('-').map((n) => parseInt(n, 10));
  if (!y || !m || !d) return undefined;
  const base = new Date(y, m - 1, d);
  const dt = new Date(base);
  dt.setDate(base.getDate() + weekday);
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}`;
}

export function adaptRoutine(r: any): Routine {
  return {
    id: String(r.id),
    name: r.name,
    start_date: r.start_date,
    days: (r.days || []).map((d: any) => ({
      id: String(d.id),
      date:
        d.date ||
        computeDateFromStart(r.start_date, typeof d.weekday === 'number' ? d.weekday : 0) ||
        computeDateFromWeekday(typeof d.weekday === 'number' ? d.weekday : 0),
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
  if (routines.length === 0) return null as any;

  // 1) Exact match today
  for (const routine of routines) {
    const day = routine.days.find((d) => d.date === target);
    if (day) {
      const weekEnd = (() => {
        const d = new Date(target + 'T00:00:00Z');
        const end = new Date(d);
        end.setDate(d.getDate() + (7 - ((d.getDay() + 6) % 7)) - 1); // Sunday of this week
        return end.toISOString().slice(0, 10);
      })();
      const future = routine.days.map((d) => d.date).filter((d) => d > target && d <= weekEnd).sort();
      const next = future[0];
      return { routine, day, next, isFallback: false } as any;
    }
  }

  // 2) Next within this week across all routines (prefer current week before jumping)
  const weekBounds = (() => {
    const d = new Date(target + 'T00:00:00Z');
    const monday = new Date(d);
    monday.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    return { start: monday.toISOString().slice(0, 10), end: sunday.toISOString().slice(0, 10) };
  })();
  type Ref = { routine: Routine; day: RoutineDay };
  const futureThisWeek: Ref[] = [];
  for (const routine of routines) {
    for (const d of routine.days) {
      if (d.date > target && d.date <= weekBounds.end) futureThisWeek.push({ routine, day: d });
    }
  }
  if (futureThisWeek.length > 0) {
    futureThisWeek.sort((a, b) => (a.day.date < b.day.date ? -1 : a.day.date > b.day.date ? 1 : 0));
    const { routine, day } = futureThisWeek[0];
    return { routine, day: undefined, next: day.date, isFallback: true } as any;
  }

  // 3) Otherwise, next across all
  const futureAll: Ref[] = [];
  for (const routine of routines) {
    for (const d of routine.days) {
      if (d.date > target) futureAll.push({ routine, day: d });
    }
  }
  if (futureAll.length > 0) {
    futureAll.sort((a, b) => (a.day.date < b.day.date ? -1 : a.day.date > b.day.date ? 1 : 0));
    const { routine, day } = futureAll[0];
    return { routine, day: undefined, next: day.date, isFallback: true } as any;
  }

  // 4) No future sessions; return earliest available overall
  const all: Ref[] = [];
  for (const routine of routines) {
    for (const d of routine.days) all.push({ routine, day: d });
  }
  if (all.length > 0) {
    all.sort((a, b) => (a.day.date < b.day.date ? -1 : a.day.date > b.day.date ? 1 : 0));
    const { routine, day } = all[0];
    return { routine, day: undefined, next: day.date, isFallback: true } as any;
  }
  return null as any;
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
  // Set start_date to Monday of current week (00:00:00Z) so UI can derive dates per week
  const now = new Date();
  const day = now.getDay();
  const mondayOffset = (day + 6) % 7;
  const monday = new Date(now);
  monday.setHours(0, 0, 0, 0);
  monday.setDate(now.getDate() - mondayOffset);
  const start_date = `${monday.getFullYear()}-${pad(monday.getMonth() + 1)}-${pad(monday.getDate())}T00:00:00Z`;
  const adapted = {
    name: payload.name,
    start_date,
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

export async function createNextWeekRoutine(routineId: string | number) {
  const r = await apiFetch<any>(`/routines/${routineId}/next-week`, { method: 'POST' });
  return adaptRoutine(r);
}

export function deleteRoutine(routineId: string | number) {
  return apiFetch<void>(`/routines/${routineId}`, { method: 'DELETE' });
}
