import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listRoutines } from '../api/routines';
import WeekView from '../features/routines/WeekView';
import DayDetail from '../features/routines/DayDetail';
import GenerateFromAI from '../features/routines/GenerateFromAI';
import { today } from '../utils/date';
import { Skeleton } from '../components/ui/Skeleton';

export default function WorkoutPage() {
  const { data, isLoading } = useQuery({ queryKey: ['routines'], queryFn: listRoutines });
  if (isLoading) {
    return (
      <div className="space-y-4 p-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-40" />
      </div>
    );
  }
  if (!data || data.length === 0) {
    return (
      <div className="p-3">
        <p>No routine found.</p>
        <GenerateFromAI />
      </div>
    );
  }
  const routine = data[data.length - 1];
  const [selected, setSelected] = useState(
    () => routine.days.find((d) => d.date === today())?.date || routine.days[0]?.date
  );
  const day = routine.days.find((d) => d.date === selected) || routine.days[0];
  return (
    <div className="space-y-4 p-3 md:p-6">
      <WeekView routine={routine} selected={selected} onSelect={setSelected} />
      {day && <DayDetail routineId={routine.id} day={day} />}
    </div>
  );
}
