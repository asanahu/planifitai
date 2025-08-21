import type { Routine, RoutineDay } from '../../api/routines';
import { completeExercise } from '../../api/routines';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { pushToast } from '../../components/ui/Toast';

interface Props {
  routineId: string;
  day: RoutineDay;
}

export default function DayDetail({ routineId, day }: Props) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (exerciseId: string) => completeExercise(routineId, day.id, exerciseId),
    onMutate: async (exerciseId) => {
      await qc.cancelQueries({ queryKey: ['routines'] });
      const prev = qc.getQueryData<Routine[]>(['routines']);
      qc.setQueryData<Routine[]>(
        ['routines'],
        (old) =>
          old?.map((r) =>
            r.id === routineId
              ? {
                  ...r,
                  days: r.days.map((d) =>
                    d.id === day.id
                      ? {
                          ...d,
                          exercises: d.exercises.map((e) =>
                            e.id === exerciseId ? { ...e, completed: true } : e
                          ),
                        }
                      : d
                  ),
                }
              : r
          ) ?? old
      );
      return { prev };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.prev) qc.setQueryData(['routines'], ctx.prev);
      pushToast('Error al completar', 'error');
    },
    onSuccess: () => pushToast('Ejercicio completado'),
    onSettled: () => qc.invalidateQueries({ queryKey: ['routines'] }),
  });
  return (
    <div className="mt-4">
      <h3 className="mb-2 font-semibold">{new Date(day.date).toDateString()}</h3>
      <ul className="space-y-2">
        {day.exercises.map((ex) => (
          <li key={ex.id} className="flex justify-between rounded border p-2">
            <span>{ex.name}</span>
            <button
              className="text-sm text-blue-500"
              disabled={ex.completed}
              onClick={() => mutation.mutate(ex.id)}
            >
              {ex.completed ? 'Done' : 'Complete'}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
