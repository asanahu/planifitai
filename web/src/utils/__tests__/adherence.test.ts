import { describe, it, expect } from 'vitest';
import { calcWeekAdherence } from '../adherence';

describe('adherence', () => {
  it('calculates 3/4 as 75%', () => {
    const active = [true, true, true, true, false, false, false];
    const workouts = [
      new Date('2024-05-13'),
      new Date('2024-05-14'),
      new Date('2024-05-15'),
    ];
    const res = calcWeekAdherence({ activeDays: active, workoutsDone: workouts });
    expect(res.countPlanned).toBe(4);
    expect(res.countDone).toBe(3);
    expect(res.rate).toBe(75);
  });
});
