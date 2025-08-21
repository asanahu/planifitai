import type { AiNutritionPlanJSON } from '../../api/ai';
import type { MealPlan } from '../../utils/storage';

export type LocalMealPlan = MealPlan;

export function mapAiNutritionPlanToLocal(ai: AiNutritionPlanJSON): LocalMealPlan {
  const plan: LocalMealPlan = {};
  (ai.days ?? []).forEach((d) => {
    const day = d.day ?? '';
    plan[day] = {} as any;
    (d.meals ?? []).forEach((m) => {
      plan[day][m.name ?? 'Meal'] = m.items ?? [];
    });
  });
  return plan;
}

export function mapAiNutritionPlanToServer(ai: AiNutritionPlanJSON) {
  return ai as unknown;
}

