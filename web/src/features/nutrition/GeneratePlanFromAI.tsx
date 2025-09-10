import { useMutation } from '@tanstack/react-query';
import { generateNutritionPlanAI } from '../../api/ai';
import { mapAiNutritionPlanToLocal } from './aiMap';
import { setMealPlan } from '../../utils/storage';
import { pushToast } from '../../components/ui/Toast';
import Overlay from '../../components/ui/Overlay';

export default function GeneratePlanFromAI() {
  const useAI = import.meta.env.VITE_FEATURE_AI === '1';
  const mutation = useMutation({
    mutationFn: async () => {
      if (!useAI) throw new Error('disabled');
      const ai = await generateNutritionPlanAI({ days: 7 });
      const local = mapAiNutritionPlanToLocal(ai);
      setMealPlan(local);
    },
    onSuccess: () => pushToast('Plan generado'),
    onError: () => pushToast('No se pudo generar plan', 'error'),
  });

  return (
    <div className="space-y-2">
      <button
        className="btn"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? 'Generando plan…' : 'Generar plan IA'}
      </button>
      {mutation.isPending && (
        <Overlay>Tu plan se está generando; analizando tu perfil, puede tardar unos minutos…</Overlay>
      )}
    </div>
  );
}
