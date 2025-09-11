import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getPlannedDayFor, completeDay, uncompleteDay, type Routine, type RoutineDay } from '../../api/routines';
import { listProgress } from '../../api/progress';
import { daysAgo, today } from '../../utils/date';
import { Skeleton } from '../../components/ui/Skeleton';
import { pushToast } from '../../components/ui/Toast';
import { calcWeekAdherence, type WeekWorkout } from '../../utils/adherence';
import { Link } from 'react-router-dom';
import { Dumbbell, Play, CheckCircle, CalendarDays } from 'lucide-react';

export function TodayWorkoutCard() {
  const dateStr = today();
  const qc = useQueryClient();
  const dayQuery = useQuery({ queryKey: ['routine-day', dateStr], queryFn: () => getPlannedDayFor(new Date(dateStr)) });
  const adherenceQuery = useQuery({
    queryKey: ['workout-progress', dateStr],
    queryFn: () => listProgress({ metric: 'workout', start: daysAgo(7), end: dateStr }),
  });

  const mutation = useMutation({
    mutationFn: async (ids: { routineId: string; dayId: string }) => completeDay(ids.routineId, ids.dayId, dateStr),
    onMutate: async () => {
      await qc.cancelQueries({ queryKey: ['routine-day', dateStr] });
      type RoutineDayData = { routine: Routine; day: RoutineDay };
      const prev = qc.getQueryData<RoutineDayData>(['routine-day', dateStr]);
      if (prev) {
        const updated: RoutineDayData = {
          ...prev,
          day: { ...prev.day, exercises: prev.day.exercises.map((e) => ({ ...e, completed: true })) },
        };
        qc.setQueryData<RoutineDayData>(['routine-day', dateStr], updated);
      }
      return { prev };
    },
    onError: (_err, _ids, ctx) => {
      if (ctx?.prev) qc.setQueryData(['routine-day', dateStr], ctx.prev);
      pushToast('Error al completar', 'error');
    },
    onSuccess: () => pushToast('Día completado'),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['routines'] });
      qc.invalidateQueries({ queryKey: ['routine'] });
      qc.invalidateQueries({ queryKey: ['workout-progress'] });
    },
  });

  if (dayQuery.isLoading) return <Skeleton className="h-40" />;
  const dataRaw = dayQuery.data as any;
  const data = dataRaw && dataRaw.isFallback ? null : dataRaw;
  const fallbackInfo = dayQuery.data && (dayQuery.data as any).isFallback ? (dayQuery.data as any) : null;
  if (!data || !data.day)
    return (
      <section className="rounded border bg-white p-3 shadow-sm dark:bg-gray-800">
        <p className="font-medium">No tienes rutina hoy</p>
        <p className="text-sm opacity-80">Hoy no hay sesión planificada.</p>
        {fallbackInfo?.next && (
          <p className="text-sm mt-1">
            Próxima sesión:{' '}
            {new Date(fallbackInfo.next).toLocaleDateString('es-ES', {
              weekday: 'long',
              day: '2-digit',
              month: 'short',
            })}
          </p>
        )}
        <div className="mt-2 flex gap-2">
          <Link
            to={fallbackInfo?.next ? `/workout?select=${encodeURIComponent(fallbackInfo.next)}` : "/workout"}
            aria-label="Ver semana de entrenamiento"
            className="inline-block rounded border px-3 py-1 text-sm"
          >
            Ver semana
          </Link>
          <Link
            to="/workout/generate"
            className="inline-block rounded bg-blue-500 px-3 py-1 text-sm text-white"
          >
            Generar plan IA
          </Link>
        </div>
      </section>
    );

  const { routine, day } = data as { routine: Routine; day: RoutineDay };
  const exercises = day.exercises;
  const allDone = exercises.every((e) => e.completed);

  const activeDays = new Array(7).fill(false);
  routine.days.forEach((d) => {
    const idx = (new Date(d.date).getDay() + 6) % 7;
    activeDays[idx] = true;
  });
  const doneSet = new Set(
    (adherenceQuery.data ?? []).map((p) => (new Date(p.date).getDay() + 6) % 7)
  );
  const workouts: WeekWorkout[] = activeDays.map((active, idx) => ({
    planned: active,
    completed: active && doneSet.has(idx),
  }));
  const adherence = calcWeekAdherence(workouts, []);
  const planned = workouts.filter((w) => w.planned).length;
  const done = workouts.filter((w) => w.completed).length;

  return (
    <section className="space-y-3 rounded border bg-white p-3 shadow-sm dark:bg-gray-800">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <Dumbbell className="h-5 w-5" /> Entrenamiento de hoy
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300">Estás a un paso de cumplir tu objetivo 💪</p>
      <ul className="space-y-1 text-sm">
        {exercises.map((ex) => (
          <li key={ex.id} className="flex items-center gap-2">
            <span className={`h-3 w-3 rounded-full ${ex.completed ? 'bg-green-500' : 'bg-gray-300'}`}></span>
            <span>{ex.name}</span>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-2">
        <Link
          to="/workout"
          aria-label="Ver semana de entrenamiento"
          className="flex h-10 items-center gap-1 rounded border px-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <CalendarDays className="h-4 w-4" /> Ver semana
        </Link>
        <Link
          to="/workout"
          aria-label="Empezar entrenamiento"
          className="flex h-10 items-center gap-1 rounded bg-blue-500 px-4 text-sm text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <Play className="h-4 w-4" /> Empezar ahora
        </Link>
        {!allDone && (
          <button
            onClick={() => mutation.mutate({ routineId: routine.id, dayId: day.id })}
            aria-label="Marcar día completado"
            className="flex h-10 items-center gap-1 rounded bg-green-500 px-4 text-sm text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <CheckCircle className="h-4 w-4" /> Marcar día completado
          </button>
        )}
        {allDone && (
          <button
            onClick={async () => {
              try {
                await uncompleteDay(routine.id, day.id, dateStr);
                pushToast('Se deshizo el día');
                qc.invalidateQueries({ queryKey: ['routine-day', dateStr] });
                qc.invalidateQueries({ queryKey: ['workout-progress'] });
              } catch (e) {
                pushToast('No se pudo deshacer', 'error');
              }
            }}
            aria-label="Deshacer completado"
            className="flex h-10 items-center gap-1 rounded border px-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            Deshacer día
          </button>
        )}
      </div>
      {allDone && (
        <p className="text-sm text-green-600">Día completado</p>
      )}
      <p className="text-sm text-gray-600 dark:text-gray-300">
        Adherencia semanal: {done}/{planned} ({adherence.workoutsPct}%)
      </p>
    </section>
  );
}
