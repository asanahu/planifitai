import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listRoutines, cloneTemplate, setActiveRoutine } from '../api/routines';
import WeekView from '../features/routines/WeekView';
import DayDetail from '../features/routines/DayDetail';
import { today } from '../utils/date';
import { Skeleton } from '../components/ui/Skeleton';
import { Link } from 'react-router-dom';
import { pushToast } from '../components/ui/Toast';

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
  const qc = useQueryClient();
  const clone = useMutation({
    mutationFn: async () => {
      const routine = await cloneTemplate(import.meta.env.VITE_FALLBACK_TEMPLATE_ID);
      await setActiveRoutine(routine.id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['routines'] });
      pushToast('Rutina creada');
    },
    onError: () => pushToast('No se pudo clonar plantilla', 'error'),
  });
  const routine = data?.[data.length - 1];
  const [selected, setSelected] = useState<string>(
    () => routine?.days.find((d) => d.date === today())?.date || routine?.days[0]?.date || today()
  );
  if (!data || data.length === 0 || !routine) {
    return (
      <div className="space-y-2 p-3">
        <p>No tienes rutina aún</p>
        {import.meta.env.VITE_FEATURE_AI === '1' && (
          <Link to="/workout/generate" className="inline-block rounded bg-blue-500 px-4 py-2 text-white">
            Generar con IA
          </Link>
        )}
        <button
          onClick={() => clone.mutate()}
          className="inline-block rounded border px-4 py-2"
        >
          Usar plantilla por defecto
        </button>
      </div>
    );
  }
  const day = routine.days.find((d) => d.date === selected) || routine.days[0];
  return (
    <div className="space-y-4 p-3 md:p-6">
      <WeekView routine={routine} selected={selected} onSelect={setSelected} />
      {day && <DayDetail routineId={routine.id} day={day} />}
    </div>
  );
}
