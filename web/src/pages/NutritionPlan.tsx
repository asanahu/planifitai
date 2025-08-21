import MealsPlan from '../features/nutrition/MealsPlan';
import GeneratePlanFromAI from '../features/nutrition/GeneratePlanFromAI';

export default function NutritionPlanPage() {
  return (
    <div className="space-y-4 p-4">
      <GeneratePlanFromAI />
      <MealsPlan />
    </div>
  );
}
