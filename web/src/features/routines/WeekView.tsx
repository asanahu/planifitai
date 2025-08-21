import type { Routine } from '../../api/routines';
import { today } from '../../utils/date';

interface Props {
  routine: Routine;
  selected: string;
  onSelect: (date: string) => void;
}

export default function WeekView({ routine, selected, onSelect }: Props) {
  const todayStr = today();
  return (
    <div className="grid grid-cols-7 gap-2">
      {routine.days.map((d) => {
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
  );
}
