import type { AiWorkoutPlanJSON } from '../../api/ai';
import type { RoutineCreatePayload } from '../../api/routines';

function parseWeekdayName(wd?: string): number | null {
  if (!wd) return null;
  const s = wd.trim().toLowerCase();
  const map: Record<string, number> = {
    monday: 0, mon: 0, lunes: 0, lun: 0,
    tuesday: 1, tue: 1, martes: 1, mar: 1,
    wednesday: 2, wed: 2, miercoles: 2, miércoles: 2, mie: 2, mié: 2,
    thursday: 3, thu: 3, jueves: 3, jue: 3,
    friday: 4, fri: 4, viernes: 4, vie: 4,
    saturday: 5, sat: 5, sabado: 5, sábado: 5, sab: 5, sáb: 5,
    sunday: 6, sun: 6, domingo: 6, dom: 6,
  };
  return map[s] ?? null;
}

export function mapAiWorkoutPlanToRoutine(
  ai: AiWorkoutPlanJSON,
  preferredWeekdays?: number[],
  equipmentByDay?: Record<number, string[]>
): RoutineCreatePayload {
  const name = ai.name ?? 'AI Routine';
  const days = (ai.days ?? []).map((day, idx) => {
    const parsed = parseWeekdayName(day.weekday);
    const weekday = parsed ?? (preferredWeekdays && preferredWeekdays[idx % preferredWeekdays.length]) ?? idx;
    return {
      weekday,
      name: (day as any).name ?? day.focus ?? `Day ${idx + 1}`,
      duration: 60,
      equipment: equipmentByDay?.[weekday],
      exercises: (day.exercises ?? []).map((ex, j) => ({
        name: ex.name ?? `Exercise ${j + 1}`,
        reps: (ex as any).reps ?? (ex as any).sets ?? 10,
        time: (ex as any).duration ?? 60,
      })),
    };
  });
  return { name, days };
}

