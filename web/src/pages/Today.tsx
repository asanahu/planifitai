import { TodayWorkoutCard } from '../features/today/TodayWorkoutCard';
import { TodayNutritionCard } from '../features/today/TodayNutritionCard';
import { QuickWeighCard } from '../features/today/QuickWeighCard';

export default function TodayPage() {
  return (
    <div className="p-4 grid gap-4 md:grid-cols-2">
      <TodayWorkoutCard />
      <TodayNutritionCard />
      <QuickWeighCard />
    </div>
  );
}
