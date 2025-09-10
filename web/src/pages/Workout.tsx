import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listRoutines, cloneTemplate, setActiveRoutine } from '../api/routines';
import WeekView from '../features/routines/WeekView';
import DayDetail from '../features/routines/DayDetail';
import { today } from '../utils/date';
import { Skeleton } from '../components/ui/Skeleton';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { pushToast } from '../components/ui/Toast';
import PageHeader from '../components/layout/PageHeader';

export default function WorkoutPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data, isLoading } = useQuery({ queryKey: ['routines'], queryFn: listRoutines });
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
  const [selected, setSelected] = useState<string>(() => today());
  useEffect(() => {
    if (!routine) return;
    const t = today();
    const pre = searchParams.get('select');
    if (pre && routine.days.some((d) => d.date === pre)) {
      setSelected(pre);
      return;
    }
    const def = routine.days.find((d) => d.date === t)?.date || routine.days[0]?.date || t;
    setSelected(def);
  }, [routine?.id, searchParams]);
  if (isLoading) {
    return (
      <div className="space-y-4 p-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-40" />
      </div>
    );
  }
  if (!data || data.length === 0 || !routine) {
    return (
      <div className="space-y-2 p-3">
        <p>No tienes rutina aún</p>
        {import.meta.env.VITE_FEATURE_AI === '1' && (
          <Link
            to="/workout/generate"
            role="button"
            aria-label="Generar con IA"
            tabIndex={0}
            className="inline-block min-h-[44px] rounded bg-blue-500 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            Generar con IA
          </Link>
        )}
        <button
          role="button"
          tabIndex={0}
          onClick={() => clone.mutate()}
          aria-label="Usar plantilla por defecto"
          className="inline-block min-h-[44px] rounded border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
        >
          Usar plantilla por defecto
        </button>
      </div>
    );
  }
  const day = routine.days.find((d) => d.date === selected) || routine.days[0];
  return (
    <div className="space-y-4 p-3 md:p-6">
      <PageHeader>
        <div className="flex items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-semibold">Rutina</h1>
            <p className="text-sm opacity-90">Planifica y sigue tus entrenamientos</p>
          </div>
          <button
            onClick={() => {
              if (data && data.length > 0) {
                const ok = window.confirm('Esto puede reemplazar tu rutina actual. ¿Continuar para regenerar con IA?');
                if (!ok) return;
              }
              navigate('/workout/generate');
            }}
            className="rounded bg-planifit-500 px-3 py-2 text-white text-sm"
          >
            Regenerar con IA
          </button>
        </div>
      </PageHeader>
      <WeekView routine={routine} selected={selected} onSelect={setSelected} />
      {day && <DayDetail routineId={routine.id} day={day} />}
    </div>
  );
}
