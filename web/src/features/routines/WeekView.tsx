import { useState } from 'react';
import type { Routine } from '../../api/routines';
import { today } from '../../utils/date';
import { calcWeekAdherence, type WeekWorkout } from '../../utils/adherence';
import { Skeleton } from '../../components/ui/Skeleton';

interface Props {
  routine?: Routine;
  selected: string;
  onSelect: (date: string) => void;
}

export default function WeekView({ routine, selected, onSelect }: Props) {
  const todayStr = today();
  const [offset, setOffset] = useState(0);
  if (!routine) return <Skeleton className="h-24" />;
  const days = routine.days.slice(offset, offset + 7);
  const workouts: WeekWorkout[] = days.map((d) => ({
    planned: true,
    completed: d.exercises.every((e) => e.completed),
  }));
  const adh = calcWeekAdherence(workouts, []);
  const planned = workouts.length;
  const done = workouts.filter((w) => w.completed).length;
  return (
    <div className="space-y-2">
      <div className="mb-2 flex justify-between text-sm">
        <button className="h-10 px-4" onClick={() => setOffset(Math.max(0, offset - 7))}>Semana anterior</button>
        <span>
          {done}/{planned} ({adh.workoutsPct}%)
        </span>
        <button className="h-10 px-4" onClick={() => setOffset(offset + 7)}>Siguiente</button>
      </div>
      <div className="grid grid-cols-7 gap-2 text-xs">
        {days.map((d) => {
          const isToday = d.date === todayStr;
          const completed = d.exercises.every((e) => e.completed);
          return (
            <button
              key={d.id}
              onClick={() => onSelect(d.date)}
              className={`rounded border p-2 ${selected === d.date ? 'bg-blue-200' : ''}`}
            >
              {new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' })}
              {isToday && ' *'}
              {completed && ' ✓'}
            </button>
          );
        })}
      </div>
    </div>
  );
}
