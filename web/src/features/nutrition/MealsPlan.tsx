import React, { useState } from 'react';
import Button from '../../components/ui/button';
import { Copy, ClipboardCheck, Eraser, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { getMealPlan, setMealPlan, getMealActuals, setMealActuals } from '../../utils/storage';
import type { MealPlan } from '../../utils/storage';

const dayKeys = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
type DayKey = (typeof dayKeys)[number];
const dayLabels: Record<DayKey, string> = {
  Mon: 'Lunes',
  Tue: 'Martes',
  Wed: 'Miércoles',
  Thu: 'Jueves',
  Fri: 'Viernes',
  Sat: 'Sábado',
  Sun: 'Domingo',
};

const mealKeys = ['Breakfast', 'Lunch', 'Dinner', 'Snack'] as const;
const mealLabels: Record<(typeof mealKeys)[number], string> = {
  Breakfast: 'Desayuno',
  Lunch: 'Comida',
  Dinner: 'Cena',
  Snack: 'Merienda',
};

function currentDayKey(): DayKey {
  const d = new Date().getDay(); // 0=Sun..6=Sat
  const map: Record<number, DayKey> = { 0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat' };
  return map[d] ?? 'Mon';
}

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
          <span key={`${it}-${idx}`} className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs">
            {it}
            <button aria-label="Eliminar" className="text-gray-500 hover:text-red-600" onClick={() => onChange(items.filter((_, j) => j !== idx))}>x</button>
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
        <Button className="rounded-full h-9" onClick={add}>Añadir</Button>
      </div>
    </div>
  );
}

export default function MealsPlan() {
  const [plan, setPlanState] = useState<MealPlan>(() => getMealPlan());
  const [actuals, setActualsState] = useState(() => getMealActuals());
  const [view, setView] = useState<'day' | 'week'>('day');
  const [selectedDay, setSelectedDay] = useState<DayKey>(() => currentDayKey());

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
    if (!confirm('Vas a borrar los registros reales de este día. ¿Continuar?')) return;
    const nextA = { ...actuals } as any;
    delete nextA[day];
    setActuals(nextA);
  };

  const copyPlanToActual = (day: string) => {
    const mealsPlan = plan[day] || {};
    const next = { ...actuals } as any;
    next[day] = Object.fromEntries(Object.entries(mealsPlan).map(([meal, items]) => [meal, [...items]]));
    setActuals(next);
  };

  const copyWeekPlanToActuals = () => {
    const next = { ...actuals } as any;
    Object.entries(plan).forEach(([d, meals]) => {
      next[d] = Object.fromEntries(Object.entries(meals as any).map(([meal, items]) => [meal, [...(items as string[])]]));
    });
    setActuals(next);
  };

  const clearWeekPlanned = () => {
    if (!confirm('Vas a borrar TODO el plan semanal. ¿Continuar?')) return;
    setPlan({});
  };
  const clearWeekActuals = () => {
    if (!confirm('Vas a borrar TODOS los registros reales de la semana. ¿Continuar?')) return;
    setActuals({} as any);
  };

  const DayCard = ({ day }: { day: DayKey }) => (
    <div>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-semibold">{dayLabels[day]}</h3>
        <div className="flex flex-wrap gap-2 text-sm">
          <Button className="h-8 px-3 rounded-full" variant="secondary" title="Copiar este día a otro" onClick={() => {
            const resp = prompt('Copiar a (día: Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo)');
            const to = resp ? (resp as string) : day;
            copyDay(day, to);
          }}><Copy className="inline mr-1 h-4 w-4"/>Copiar día a otro</Button>
        <Button className="h-8 px-3 rounded-full" title="Marcar plan como real para este día" onClick={() => copyPlanToActual(day)}><ClipboardCheck className="inline mr-1 h-4 w-4"/>Copiar Plan a Real</Button>
        </div>
      </div>
      <div className="mb-3 text-xs text-gray-600">
        {(() => {
          const plannedCount = mealKeys.reduce((acc, mk) => acc + ((plan[day]?.[mk] || []).length), 0);
          const eatenCount = mealKeys.reduce((acc, mk) => acc + ((((actuals as any)[day]?.[mk]) || []).length), 0);
          const diff = eatenCount - plannedCount;
          const sign = diff > 0 ? '+' : '';
          return `Resumen: Planificados ${plannedCount} - Reales ${eatenCount} - Dif ${sign}${diff}`;
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
                  <div className="mb-1 text-xs uppercase tracking-wide text-gray-500">Real</div>
                  <ItemsEditor
                    items={eaten}
                    onChange={(next) => {
                      const a = { ...(actuals as any) };
                      if (!a[day]) a[day] = {};
                      a[day][meal] = next;
                      setActuals(a);
                    }}
                    placeholder="Añadir alimento real..."
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button className="h-8 px-3 rounded-full" variant="ghost" title="Vaciar planificado de este día" onClick={() => clearDayPlanned(day)}><Eraser className="inline mr-1 h-4 w-4"/>Limpiar plan</Button>
                <Button className="h-8 px-3 rounded-full" variant="ghost" title="Vaciar real de este día" onClick={() => clearDayActual(day)}><Trash2 className="inline mr-1 h-4 w-4"/>Limpiar real</Button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded border p-3 bg-white dark:bg-gray-900 shadow-sm">
        <div className="text-sm opacity-80">Acciones semanales</div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={copyWeekPlanToActuals} className="h-9 rounded-full" title="Copiar plan a real (semana)"><ClipboardCheck className="inline mr-2 h-4 w-4"/>Copiar plan a real</Button>
          <Button onClick={clearWeekPlanned} className="h-9 rounded-full" variant="secondary" title="Vaciar todos los días planificados"><Eraser className="inline mr-2 h-4 w-4"/>Limpiar planificado</Button>
          <Button onClick={clearWeekActuals} className="h-9 rounded-full" variant="ghost" title="Vaciar todos los registros reales"><Trash2 className="inline mr-2 h-4 w-4"/>Limpiar real</Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm opacity-80">Vista:</span>
        <Button variant={view==='day' ? 'secondary' : 'ghost'} className="h-8" onClick={() => setView('day')}>Díario</Button>
        <Button variant={view==='week' ? 'secondary' : 'ghost'} className="h-8" onClick={() => setView('week')}>Semanal</Button>
        {view === 'day' && (
          <>
            <span className="ml-4 text-sm opacity-80">Día:</span>
            <div className="flex flex-wrap items-center gap-1">
              <Button className="h-8 px-2" variant="ghost" onClick={() => { const i=dayKeys.indexOf(selectedDay); setSelectedDay(dayKeys[(i-1+dayKeys.length)%dayKeys.length]); }} aria-label="Anterior"><ChevronLeft className="inline h-4 w-4"/></Button>
              {dayKeys.map((d) => (
                <Button key={d} className="h-8 px-3" variant={selectedDay===d ? 'secondary' : 'ghost'} onClick={() => { setSelectedDay(d); }}>{dayLabels[d]}</Button>
              ))}
              <Button className="h-8 px-2" variant="ghost" onClick={() => { const i=dayKeys.indexOf(selectedDay); setSelectedDay(dayKeys[(i+1)%dayKeys.length]); }} aria-label="Siguiente"><ChevronRight className="inline h-4 w-4"/></Button>
            </div>
          </>
        )}
      </div>

      {view === 'week' && (
        <div className="space-y-4">
          {dayKeys.map((day) => (
            <div key={day} className="rounded-lg border p-3 bg-white dark:bg-gray-900 shadow-sm">
              <DayCard day={day} />
            </div>
          ))}
        </div>
      )}

      {view === 'day' && (
        <div className="max-w-3xl mx-auto">
          <div className="rounded-lg border p-3 bg-white dark:bg-gray-900 shadow-sm">
            <DayCard day={selectedDay} />
          </div>
        </div>
      )}
    </div>
  );
}
