import MealsToday from '../features/nutrition/MealsToday';
import PageHeader from '../components/layout/PageHeader';

export default function NutritionTodayPage() {
  return (
    <div className="space-y-3 p-4" data-testid="nutrition-today-page">
      <PageHeader>
        <h1 className="text-xl font-semibold">Nutrición de hoy</h1>
        <p className="text-sm opacity-90">Registra comidas y controla tus objetivos</p>
      </PageHeader>
      <MealsToday />
    </div>
  );
}
