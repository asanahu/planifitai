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
          <ul className="space-y-2">
            {meals.map((meal) => {
              const items = plan[day]?.[meal] || [];
              return (
                <li key={meal} className="space-y-1">
                  <div className="flex justify-between">
                    <span>{meal}</span>
                    <button
                      className="text-sm text-blue-500"
                      onClick={() => update(day, meal)}
                    >
                      Editar
                    </button>
                  </div>
                  {items.length > 0 ? (
                    <ul className="list-disc pl-5 text-sm text-gray-800">
                      {items.map((it, idx) => (
                        <li key={`${meal}-${idx}`}>{it}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-sm text-gray-500">Sin items</div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
