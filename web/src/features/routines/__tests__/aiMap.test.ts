import { describe, it, expect } from 'vitest';
import { mapAiWorkoutPlanToRoutine } from '../aiMap';

describe('mapAiWorkoutPlanToRoutine', () => {
  it('maps full plan', () => {
    const routine = mapAiWorkoutPlanToRoutine({
      name: 'Plan',
      days: [
        { name: 'D1', exercises: [{ name: 'Ex', reps: 5, duration: 30 }] },
      ],
    });
    expect(routine.name).toBe('Plan');
    expect(routine.days[0].exercises[0].reps).toBe(5);
  });

  it('fills defaults', () => {
    const routine = mapAiWorkoutPlanToRoutine({});
    expect(routine.name).toBeTruthy();
    expect(routine.days).toEqual([]);
  });
});
