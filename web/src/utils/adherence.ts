export interface WeekWorkout {
  planned: boolean;
  completed: boolean;
}

export interface WeekMeal {
  target: number;
  calories: number;
}

export function calcWeekAdherence(
  workouts: WeekWorkout[],
  meals: WeekMeal[]
) {
  const planned = workouts.filter((w) => w.planned).length;
  const done = workouts.filter((w) => w.planned && w.completed).length;
  const workoutsPct = planned === 0 ? 0 : Math.round((done / planned) * 100);

  const mealDays = meals.filter((m) => m.target > 0).length;
  const mealOk = meals.filter((m) => m.target > 0 && m.calories <= m.target).length;
  const nutritionPct = mealDays === 0 ? 0 : Math.round((mealOk / mealDays) * 100);

  const overallPct = Math.round((workoutsPct + nutritionPct) / 2);

  return { workoutsPct, nutritionPct, overallPct };
}
