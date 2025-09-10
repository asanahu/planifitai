import { useState } from 'react';
import type React from 'react';
import { getMealPlan, setMealPlan, getMealActuals, setMealActuals } from '../../utils/storage';
import type { MealPlan } from '../../utils/storage';

const dayKeys = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
const dayLabels: Record<(typeof dayKeys)[number], string> = {
  Mon: 'Lun',
  Tue: 'Mar',
  Wed: 'Mié',
  Thu: 'Jue',
  Fri: 'Vie',
  Sat: 'Sáb',
  Sun: 'Dom',
};
const esToKey: Record<string, (typeof dayKeys)[number]> = {
  Lun: 'Mon',
  Mar: 'Tue',
  'Mié': 'Wed',
  Mie: 'Wed',
  Jue: 'Thu',
  Vie: 'Fri',
  'Sáb': 'Sat',
  Sab: 'Sat',
  Dom: 'Sun',
};

const mealKeys = ['Breakfast', 'Lunch', 'Dinner', 'Snack'] as const;
const mealLabels: Record<(typeof mealKeys)[number], string> = {
  Breakfast: 'Desayuno',
  Lunch: 'Comida',
  Dinner: 'Cena',
  Snack: 'Merienda',
};

function ItemsEditor({
  items,
  onChange,
  placeholder,
}: {
  items: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}) {
  const [val, setVal] = useState('');
  const add = () => {
    const v = val.trim();
    if (!v) return;
    onChange([...items, v]);
    setVal('');
  };
  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      add();
    }
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {items.map((it, idx) => (
          <span
            key={`${it}-${idx}`}
            className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs"
          >
            {it}
            <button
              aria-label="Eliminar"
              className="text-gray-500 hover:text-red-600"
              onClick={() => onChange(items.filter((_, j) => j !== idx))}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="w-full rounded border px-3 py-2 text-sm"
          placeholder={placeholder || 'Añadir alimento...'}
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={onKey}
        />
        <button className="rounded bg-blue-500 px-3 py-2 text-white" onClick={add}>
          Añadir
        </button>
      </div>
    </div>
  );
}

export default function MealsPlan() {
  const [plan, setPlanState] = useState<MealPlan>(() => getMealPlan());
  const [actuals, setActualsState] = useState(() => getMealActuals());

  const setPlan = (p: MealPlan) => {
    setPlanState(p);
    setMealPlan(p);
  };
  const setActuals = (a: Record<string, Record<string, string[]>>) => {
    setActualsState(a);
    setMealActuals(a);
  };

  const copyDay = (from: string, to: string) => {
    const next = { ...plan, [to]: { ...plan[from] } };
    setPlan(next);
    const nextA = { ...actuals, [to]: { ...(actuals as any)[from] } } as any;
    setActuals(nextA);
  };

  const clearDayPlanned = (day: string) => {
    if (!confirm('Vas a borrar el planificado de este día. ¿Continuar?')) return;
    const next = { ...plan } as any;
    delete next[day];
    setPlan(next);
  };

  const clearDayActual = (day: string) => {
    if (!confirm('Vas a borrar lo comido de este día. ¿Continuar?')) return;
    const nextA = { ...actuals } as any;
    delete nextA[day];
    setActuals(nextA);
  };

  const copyPlanToActual = (day: string) => {
    const mealsPlan = plan[day] || {};
    const next = { ...actuals } as any;
    next[day] = Object.fromEntries(
      Object.entries(mealsPlan).map(([meal, items]) => [meal, [...items]])
    );
    setActuals(next);
  };

  return (
    <div className="space-y-4">
      {dayKeys.map((day) => (
        <div key={day} className="rounded border p-3">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-base font-semibold">{dayLabels[day]}</h3>
            <div className="space-x-2 text-sm">
              <button onClick={() => {
                const resp = prompt('Copiar a (abbr día: Lun, Mar, Mié, Jue, Vie, Sáb, Dom)');
                const to = resp ? (esToKey[resp] || (resp as any)) : day;
                copyDay(day, to as string);
              }}>Copiar</button>
              <button onClick={() => copyPlanToActual(day)}>Copiar plan a comido</button>
              <button onClick={() => clearDayPlanned(day)}>Limpiar planificado</button>
              <button onClick={() => clearDayActual(day)}>Limpiar comido</button>
            </div>
          </div>
          <div className="mb-3 text-xs text-gray-600">
            {(() => {
              const plannedCount = mealKeys.reduce((acc, mk) => acc + ((plan[day]?.[mk] || []).length), 0);
              const eatenCount = mealKeys.reduce((acc, mk) => acc + ((((actuals as any)[day]?.[mk]) || []).length), 0);
              const diff = eatenCount - plannedCount;
              const sign = diff > 0 ? '+' : '';
              return `Resumen: Planificados ${plannedCount} · Comidos ${eatenCount} · Dif ${sign}${diff}`;
            })()}
          </div>
          <ul className="space-y-4">
            {mealKeys.map((meal) => {
              const planned = plan[day]?.[meal] || [];
              const eaten = (actuals as any)[day]?.[meal] || [];
              return (
                <li key={meal} className="space-y-2">
                  <div className="font-medium">{mealLabels[meal]}</div>
                  <div className="grid gap-4 md:grid-cols-2 md:divide-x md:divide-gray-200">
                    <div className="md:pr-4">
                      <div className="mb-1 text-xs uppercase tracking-wide text-gray-500">Planificado</div>
                      <ItemsEditor
                        items={planned}
                        onChange={(next) => {
                          const p = { ...plan } as any;
                          if (!p[day]) p[day] = {};
                          p[day][meal] = next;
                          setPlan(p);
                        }}
                        placeholder="Añadir alimento planificado..."
                      />
                    </div>
                    <div className="md:pl-4">
                      <div className="mb-1 text-xs uppercase tracking-wide text-gray-500">Comido</div>
                      <ItemsEditor
                        items={eaten}
                        onChange={(next) => {
                          const a = { ...(actuals as any) };
                          if (!a[day]) a[day] = {};
                          a[day][meal] = next;
                          setActuals(a);
                        }}
                        placeholder="Añadir alimento comido..."
                      />
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
