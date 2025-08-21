import { useMutation, useQuery } from '@tanstack/react-query';
import { getPlannedDayFor, completeDay } from '../../api/routines';
import { listProgress } from '../../api/progress';
import { daysAgo, today } from '../../utils/date';
import { Skeleton } from '../../components/ui/Skeleton';
import { pushToast } from '../../components/ui/Toast';
import { calcWeekAdherence } from '../../utils/adherence';

export function TodayWorkoutCard() {
  const dateStr = today();
  const dayQuery = useQuery({ queryKey: ['routine-day', dateStr], queryFn: () => getPlannedDayFor(new Date(dateStr)) });
  const adherenceQuery = useQuery({
    queryKey: ['workout-progress', dateStr],
    queryFn: () => listProgress({ metric: 'workout', start: daysAgo(7), end: dateStr }),
  });

  const mutation = useMutation({
    mutationFn: async (ids: { routineId: string; dayId: string }) => completeDay(ids.routineId, ids.dayId),
    onSuccess: () => {
      pushToast('Día completado');
      dayQuery.refetch();
    },
    onError: () => pushToast('Error al completar', 'error'),
  });

  if (dayQuery.isLoading) return <Skeleton className="h-32" />;
  const data = dayQuery.data;
  if (!data) return <section className="border p-4 rounded">No tienes rutina hoy</section>;

  const { routine, day } = data;
  const exercises = day.exercises;
  const allDone = exercises.every((e) => e.completed);

  const activeDays = new Array(7).fill(false);
  routine.days.forEach((d) => {
    const idx = (new Date(d.date).getDay() + 6) % 7;
    activeDays[idx] = true;
  });
  const adherence = calcWeekAdherence({
    activeDays,
    workoutsDone: (adherenceQuery.data ?? []).map((p) => new Date(p.date)),
  });

  return (
    <section className="border p-4 rounded space-y-2">
      <h2 className="font-bold">Entrenamiento de hoy</h2>
      <ul className="space-y-1">
        {exercises.map((ex) => (
          <li key={ex.id} className="flex items-center space-x-2">
            <span className={`w-3 h-3 rounded-full ${ex.completed ? 'bg-green-500' : 'bg-gray-300'}`}></span>
            <span>{ex.name}</span>
          </li>
        ))}
      </ul>
      {allDone ? (
        <p className="text-sm text-green-600">Día completado</p>
      ) : (
        <button
          onClick={() => mutation.mutate({ routineId: routine.id, dayId: day.id })}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Marcar día completado
        </button>
      )}
      <p className="text-sm text-gray-600">
        Adherencia semanal: {adherence.countDone}/{adherence.countPlanned} ({adherence.rate}%)
      </p>
    </section>
  );
}
