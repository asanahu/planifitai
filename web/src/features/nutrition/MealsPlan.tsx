import { useState } from 'react';
import { getMealPlan, setMealPlan } from '../../utils/storage';
import type { MealPlan } from '../../utils/storage';

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const meals = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

export default function MealsPlan() {
  const [plan, setPlanState] = useState<MealPlan>(() => getMealPlan());

  const update = (day: string, meal: string) => {
    const items = prompt('Items (comma separated)', plan[day]?.[meal]?.join(',') || '');
    if (items !== null) {
      const next = { ...plan };
      if (!next[day]) next[day] = {} as any;
      next[day][meal] = items ? items.split(',').map((s) => s.trim()) : [];
      setPlan(next);
    }
  };

  const setPlan = (p: MealPlan) => {
    setPlanState(p);
    setMealPlan(p);
  };

  const copyDay = (from: string, to: string) => {
    const next = { ...plan, [to]: { ...plan[from] } };
    setPlan(next);
  };

  const clearDay = (day: string) => {
    const next = { ...plan };
    delete next[day];
    setPlan(next);
  };

  return (
    <div className="space-y-4">
      {days.map((day) => (
        <div key={day} className="rounded border p-2">
          <div className="mb-2 flex justify-between">
            <h3 className="font-semibold">{day}</h3>
            <div className="space-x-2 text-sm">
              <button onClick={() => copyDay(day, prompt('Copiar a (day abbr)') || day)}>Copiar</button>
              <button onClick={() => clearDay(day)}>Limpiar</button>
            </div>
          </div>
          <ul className="space-y-1">
            {meals.map((meal) => (
              <li key={meal} className="flex justify-between">
                <span>{meal}</span>
                <button className="text-sm text-blue-500" onClick={() => update(day, meal)}>
                  {plan[day]?.[meal]?.length || 0} items
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
