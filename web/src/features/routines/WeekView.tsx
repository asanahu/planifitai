import { useMemo } from 'react';
import type { Routine } from '../../api/routines';
import { today } from '../../utils/date';
import { calcWeekAdherence, type WeekWorkout } from '../../utils/adherence';
import { Skeleton } from '../../components/ui/Skeleton';
import { pushToast } from '../../components/ui/Toast';
import { ChevronLeft, ChevronRight, CalendarDays, CheckCircle2 } from 'lucide-react';

interface Props {
  routine?: Routine;
  selected: string;
  onSelect: (date: string) => void;
  onPrevWeek?: () => void;
  onNextWeek?: () => void;
}

export default function WeekView({ routine, selected, onSelect, onPrevWeek, onNextWeek }: Props) {
  const todayStr = today();
  if (!routine) return <Skeleton className="h-24" />;
  const days = routine.days;
  const workouts: WeekWorkout[] = days.map((d) => ({
    planned: true,
    completed: d.exercises.every((e) => e.completed),
  }));
  const adh = calcWeekAdherence(workouts, []);
  const planned = workouts.length;
  const done = workouts.filter((w) => w.completed).length;
  const weekStart = useMemo(() => {
    if (routine.start_date) return new Date(routine.start_date);
    const minDate = days.reduce((min, d) => (d.date < min ? d.date : min), days[0]?.date);
    return new Date(minDate + 'T00:00:00Z');
  }, [routine.start_date, days]);
  const weekEnd = useMemo(() => {
    const d = new Date(weekStart);
    d.setDate(weekStart.getDate() + 6);
    return d;
  }, [weekStart]);
  return (
    <div className="space-y-2">
      <div className="mb-2 flex items-center justify-between text-sm">
        <button
          className="flex items-center gap-1 rounded-md border px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800"
          onClick={() => onPrevWeek?.()}
        >
          <ChevronLeft className="h-4 w-4" /> Anterior
        </button>
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 font-medium">
            <CalendarDays className="h-4 w-4" />
            Semana del {weekStart.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
            &nbsp;al&nbsp;
            {weekEnd.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
          </div>
          <div className="opacity-80 text-xs mt-0.5">{done}/{planned} completados ({adh.workoutsPct}%)</div>
        </div>
        <button
          className="flex items-center gap-1 rounded-md border px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800"
          onClick={() => onNextWeek?.()}
        >
          Siguiente <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-2 text-xs">
        {days.map((d) => {
          const isToday = d.date === todayStr;
          const completed = d.exercises.every((e) => e.completed);
          return (
            <button
              key={d.id}
              onClick={() => onSelect(d.date)}
              className={[
                'group rounded-xl border p-3 text-center shadow-sm transition',
                'hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500',
                selected === d.date ? 'ring-2 ring-planifit-500' : '',
                completed ? 'border-green-500/60' : 'border-gray-200 dark:border-gray-800',
              ].join(' ')}
            >
              <div className="text-[11px] opacity-80">
                {new Date(d.date).toLocaleDateString('es-ES', { weekday: 'short' })}
              </div>
              <div className="text-sm font-medium">
                {new Date(d.date).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' })}
              </div>
              <div className="mt-1 h-4">
                {isToday && <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] text-blue-700">Hoy</span>}
                {completed && (
                  <span className="inline-flex items-center gap-1 text-[10px] text-green-600">
                    <CheckCircle2 className="h-3 w-3" /> Hecho
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
