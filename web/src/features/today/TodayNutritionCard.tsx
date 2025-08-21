import { useQuery } from '@tanstack/react-query';
import { getDayLog } from '../../api/nutrition';
import { today } from '../../utils/date';
import { Skeleton } from '../../components/ui/Skeleton';
import { Link } from 'react-router-dom';

export function TodayNutritionCard() {
  const date = today();
  const { data, isLoading } = useQuery({ queryKey: ['nutrition', date], queryFn: () => getDayLog(date) });
  if (isLoading) return <Skeleton className="h-32" />;
  if (!data) return <section className="border p-4 rounded">No hay comidas registradas</section>;
  const consumed = data.totals.calories;
  const target = data.targets.calories;
  const percent = target ? Math.round((consumed / target) * 100) : 0;
  return (
    <section className="border p-4 rounded space-y-2">
      <h2 className="font-bold">Nutrición</h2>
      <p>{consumed} / {target} kcal ({percent}%)</p>
      <div className="flex space-x-2 text-sm">
        <Link className="text-blue-600" to="/nutrition/today">Editar comidas de hoy</Link>
        <Link className="text-blue-600" to="/shopping-list">Lista de la compra</Link>
      </div>
    </section>
  );
}
