import { describe, it, expect } from 'vitest';
import { calcWeekAdherence, type WeekMeal, type WeekWorkout } from '../adherence';

describe('adherence', () => {
  it('calculates workouts and nutrition adherence', () => {
    const workouts: WeekWorkout[] = [
      { planned: true, completed: true },
      { planned: true, completed: true },
      { planned: true, completed: false },
      { planned: true, completed: true },
      { planned: false, completed: false },
      { planned: false, completed: false },
      { planned: false, completed: false },
    ];
    const meals: WeekMeal[] = [
      { target: 2000, calories: 1900 },
      { target: 2000, calories: 2100 },
      { target: 2000, calories: 1800 },
      { target: 0, calories: 0 },
      { target: 2000, calories: 1900 },
      { target: 2000, calories: 2000 },
      { target: 0, calories: 0 },
    ];
    const res = calcWeekAdherence(workouts, meals);
    expect(res.workoutsPct).toBe(75);
    expect(res.nutritionPct).toBe(80);
    expect(res.overallPct).toBe(78);
  });
});
