import MealsPlan from '../features/nutrition/MealsPlan';
import GeneratePlanFromAI from '../features/nutrition/GeneratePlanFromAI';
import Card from '../components/ui/card';
import PageHeader from '../components/layout/PageHeader';

export default function NutritionPlanPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <PageHeader className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Plan semanal</h1>
          <p className="text-sm opacity-90">Genera o edita tu planificación de comidas para la semana</p>
        </div>
        <GeneratePlanFromAI />
      </PageHeader>
      <Card>
        <MealsPlan />
      </Card>
    </div>
  );
}


