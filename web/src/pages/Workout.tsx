import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listRoutines } from '../api/routines';
import WeekView from '../features/routines/WeekView';
import DayDetail from '../features/routines/DayDetail';
import GenerateFromAI from '../features/routines/GenerateFromAI';
import { today } from '../utils/date';

export default function WorkoutPage() {
  const { data } = useQuery({ queryKey: ['routines'], queryFn: listRoutines });
  if (!data || data.length === 0) {
    return (
      <div className="p-4">
        <p>No routine found.</p>
        <GenerateFromAI />
      </div>
    );
  }
  const routine = data[data.length - 1];
  const [selected, setSelected] = useState(() => routine.days.find((d) => d.date === today())?.date || routine.days[0]?.date);
  const day = routine.days.find((d) => d.date === selected) || routine.days[0];
  return (
    <div className="p-4 space-y-4">
      <WeekView routine={routine} selected={selected} onSelect={setSelected} />
      {day && <DayDetail routineId={routine.id} day={day} />}
    </div>
  );
}
