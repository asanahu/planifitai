import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listRoutines, cloneTemplate, setActiveRoutine } from '../api/routines';
import WeekView from '../features/routines/WeekView';
import DayDetail from '../features/routines/DayDetail';
import { today } from '../utils/date';
import { Skeleton } from '../components/ui/Skeleton';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { pushToast } from '../components/ui/Toast';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/card';
import Button from '../components/ui/button';
import { Activity, Sparkles, CalendarRange, CheckCircle2 } from 'lucide-react';
import { calcWeekAdherence, type WeekWorkout } from '../utils/adherence';

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
  const [routineIdx, setRoutineIdx] = useState<number>(0);
  const routines = data || [];
  const routine = routines[routines.length > 0 ? routineIdx : 0];
  const [selected, setSelected] = useState<string>(() => today());
  useEffect(() => {
    if (routines.length === 0) return;
    // Si la última parece ser "Semana siguiente", por defecto muestra la anterior
    const last = routines[routines.length - 1];
    const isNextWeek = typeof (last as any).name === 'string' && (last as any).name.toLowerCase().includes('semana siguiente');
    setRoutineIdx(isNextWeek && routines.length >= 2 ? routines.length - 2 : routines.length - 1);
  }, [routines.length]);

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
      <div className="p-4 md:p-8">
        <div className="mx-auto max-w-3xl">
          <PageHeader className="mb-4">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-white/20 p-2"><Activity className="h-6 w-6" /></div>
              <div>
                <h2 className="text-2xl font-semibold">Entrenamiento</h2>
                <p className="text-sm opacity-90">Crea tu primera rutina para empezar</p>
              </div>
            </div>
          </PageHeader>
          <Card className="text-center">
            <div className="mx-auto mb-3 grid h-16 w-16 place-items-center rounded-full bg-planifit-50 text-planifit-600">
              <Activity className="h-8 w-8" />
            </div>
            <p className="mb-1 text-lg font-medium">No tienes rutina aún</p>
            <p className="mx-auto mb-4 max-w-md text-sm opacity-80">
              Genera una rutina adaptada a ti o empieza con nuestra plantilla base.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {import.meta.env.VITE_FEATURE_AI === '1' && (
                <Link to="/workout/generate" role="button" aria-label="Generar con IA" tabIndex={0}>
                  <Button className="inline-flex items-center gap-2">
                    <Sparkles className="h-4 w-4" /> Generar con IA
                  </Button>
                </Link>
              )}
              <button
                role="button"
                tabIndex={0}
                onClick={() => clone.mutate()}
                aria-label="Usar plantilla por defecto"
                className="inline-flex items-center gap-2 rounded-md border px-4 py-2 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500"
              >
                <CalendarRange className="h-4 w-4" /> Usar plantilla por defecto
              </button>
            </div>
          </Card>
        </div>
      </div>
    );
  }
  const day = routine.days.find((d) => d.date === selected) || routine.days[0];
  // Quick stats for the header
  const workouts: WeekWorkout[] = useMemo(
    () => routine.days.map((d) => ({ planned: true, completed: d.exercises.every((e) => e.completed) })),
    [routine?.id]
  );
  const planned = workouts.length;
  const done = workouts.filter((w) => w.completed).length;
  const adh = calcWeekAdherence(workouts, []);
  return (
    <div className="p-3 md:p-6">
      <div className="mx-auto max-w-6xl space-y-4">
        <PageHeader className="animate-fade-in">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Entrenamiento</h1>
              <p className="text-sm opacity-90">Planifica y sigue tus entrenamientos</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1 text-sm animate-slide-up" style={{ animationDelay: '80ms' }}>
                <CheckCircle2 className="h-4 w-4" /> {done}/{planned} completados
              </div>
              <div className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1 text-sm animate-slide-up" style={{ animationDelay: '160ms' }}>
                <Activity className="h-4 w-4" /> Adherencia {adh.workoutsPct}%
              </div>
              <Button
                variant="secondary"
                className="group inline-flex items-center gap-2 bg-white/10 text-white hover:bg-white/20 transition-transform hover:scale-[1.02] animate-slide-up"
                onClick={() => navigate('/workout/generate')}
              >
                <Sparkles className="h-4 w-4 animate-soft-pulse" /> Generar con IA
              </Button>
            </div>
          </div>
        </PageHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="p-3 md:p-4">
            <WeekView
              routine={routine}
              selected={selected}
              onSelect={setSelected}
              onPrevWeek={() => routines.length > 0 && setRoutineIdx(Math.max(0, routineIdx - 1))}
              onNextWeek={() => routines.length > 0 && setRoutineIdx(Math.min(routines.length - 1, routineIdx + 1))}
            />
          </Card>
          <Card className="p-3 md:p-4">
            {day && <DayDetail routineId={routine.id} day={day} />}
          </Card>
        </div>
      </div>
    </div>
  );
}
