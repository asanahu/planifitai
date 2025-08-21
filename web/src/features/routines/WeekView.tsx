import { useState } from 'react';
import type { Routine } from '../../api/routines';
import { today } from '../../utils/date';
import { calcWeekAdherence } from '../../utils/adherence';

interface Props {
  routine: Routine;
  selected: string;
  onSelect: (date: string) => void;
}

export default function WeekView({ routine, selected, onSelect }: Props) {
  const todayStr = today();
  const [offset, setOffset] = useState(0);
  const days = routine.days.slice(offset, offset + 7);
  const activeDays = days.map(() => true);
  const workoutsDone = days
    .filter((d) => d.exercises.every((e) => e.completed))
    .map((d) => new Date(d.date));
  const adh = calcWeekAdherence({ activeDays, workoutsDone });
  return (
    <div>
      <div className="flex justify-between mb-2 text-sm">
        <button onClick={() => setOffset(Math.max(0, offset - 7))}>Semana anterior</button>
        <span>
          {adh.countDone}/{adh.countPlanned} ({adh.rate}%)
        </span>
        <button onClick={() => setOffset(offset + 7)}>Siguiente</button>
      </div>
      <div className="grid grid-cols-7 gap-2">
        {days.map((d) => {
          const isToday = d.date === todayStr;
          const completed = d.exercises.every((e) => e.completed);
          return (
            <button
              key={d.id}
              onClick={() => onSelect(d.date)}
              className={`p-2 border rounded text-sm ${selected === d.date ? 'bg-blue-200' : ''}`}
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
