import { useMutation } from '@tanstack/react-query';
import { generateNutritionPlanAI } from '../../api/ai';
import { mapAiNutritionPlanToLocal } from './aiMap';
import { setMealPlan } from '../../utils/storage';
import { pushToast } from '../../components/ui/Toast';

export default function GeneratePlanFromAI() {
  const useAI = import.meta.env.VITE_USE_AI_NUTRITION_GENERATOR === 'true';
  const mutation = useMutation({
    mutationFn: async () => {
      if (!useAI) throw new Error('disabled');
      const ai = await generateNutritionPlanAI();
      const local = mapAiNutritionPlanToLocal(ai);
      setMealPlan(local);
    },
    onSuccess: () => pushToast('Plan generado'),
    onError: () => pushToast('No se pudo generar plan', 'error'),
  });

  return (
    <button className="btn" onClick={() => mutation.mutate()}>
      Generar plan IA
    </button>
  );
}

