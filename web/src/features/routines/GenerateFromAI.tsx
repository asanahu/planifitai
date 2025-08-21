import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { generateWorkoutPlanAI } from '../../api/ai';
import { mapAiWorkoutPlanToRoutine } from './aiMap';
import { createRoutine, setActiveRoutine, type RoutineCreatePayload } from '../../api/routines';
import { pushToast } from '../../components/ui/Toast';

export default function GenerateFromAI() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const useAI = import.meta.env.VITE_USE_AI_WORKOUT_GENERATOR === 'true';

  const fallback: RoutineCreatePayload = {
    name: 'Full Body 3d',
    days: [0, 2, 4].map((weekday) => ({
      weekday,
      name: 'Full Body',
      duration: 60,
      exercises: [{ name: 'Push Ups', reps: 10, time: 60 }],
    })),
  };

  const mutation = useMutation({
    mutationFn: async () => {
      try {
        if (!useAI) throw new Error('disabled');
        const ai = await generateWorkoutPlanAI();
        const payload = mapAiWorkoutPlanToRoutine(ai);
        const routine = await createRoutine(payload);
        await setActiveRoutine(routine.id);
        return routine;
      } catch {
        const routine = await createRoutine(fallback);
        pushToast('Usando rutina por defecto', 'error');
        return routine;
      }
    },
    onSuccess: (routine) => {
      qc.invalidateQueries({ queryKey: ['routines'] });
      qc.invalidateQueries({ queryKey: ['routine', routine.id] });
      pushToast('Rutina generada');
      navigate('/workout');
    },
    onError: () => pushToast('No se pudo generar rutina', 'error'),
  });

  return (
    <button className="btn" onClick={() => mutation.mutate()}>
      Generar plan IA
    </button>
  );
}
