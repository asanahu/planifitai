import type { RoutineDay } from '../../api/routines';
import { completeExercise } from '../../api/routines';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Props {
  routineId: string;
  day: RoutineDay;
}

export default function DayDetail({ routineId, day }: Props) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (exerciseId: string) => completeExercise(routineId, day.id, exerciseId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['routines'] })
  });
  return (
    <div className="mt-4">
      <h3 className="mb-2 font-semibold">{new Date(day.date).toDateString()}</h3>
      <ul className="space-y-2">
        {day.exercises.map((ex) => (
          <li key={ex.id} className="flex justify-between border p-2 rounded">
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
