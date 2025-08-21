import type { AiWorkoutPlanJSON } from '../../api/ai';
import type { RoutineCreatePayload } from '../../api/routines';

export function mapAiWorkoutPlanToRoutine(ai: AiWorkoutPlanJSON): RoutineCreatePayload {
  const name = ai.name ?? 'AI Routine';
  const days = (ai.days ?? []).map((day, idx) => ({
    weekday: idx,
    name: day.name ?? `Day ${idx + 1}`,
    duration: 60,
    exercises: (day.exercises ?? []).map((ex, j) => ({
      name: ex.name ?? `Exercise ${j + 1}`,
      reps: ex.reps ?? ex.sets ?? 10,
      time: ex.duration ?? 60,
    })),
  }));
  return { name, days };
}

