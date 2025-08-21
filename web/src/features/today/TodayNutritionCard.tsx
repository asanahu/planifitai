import { useQuery } from '@tanstack/react-query';
import { getDayLog } from '../../api/nutrition';
import { today } from '../../utils/date';
import { Skeleton } from '../../components/ui/Skeleton';
import { Link } from 'react-router-dom';
import { Utensils, PlusCircle, CalendarDays, ShoppingCart } from 'lucide-react';

export function TodayNutritionCard() {
  const date = today();
  const { data, isLoading } = useQuery({ queryKey: ['nutrition', date], queryFn: () => getDayLog(date) });
  if (isLoading) return <Skeleton className="h-40" />;
  if (!data)
    return (
      <section className="space-y-3 rounded border bg-white p-3 shadow-sm dark:bg-gray-800">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <Utensils className="h-5 w-5" /> Comidas de hoy
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-300">Aún no has registrado comidas</p>
        <Link
          to="/nutrition/today"
          className="flex h-10 items-center gap-1 rounded bg-blue-500 px-4 text-white"
        >
          <PlusCircle className="h-4 w-4" /> Añadir comida
        </Link>
      </section>
    );
  const consumed = data.totals.calories;
  const target = data.targets.calories;
  const percent = target ? Math.round((consumed / target) * 100) : 0;
  return (
    <section className="space-y-3 rounded border bg-white p-3 shadow-sm dark:bg-gray-800">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <Utensils className="h-5 w-5" /> Comidas de hoy
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        Buen ritmo, estás en el {percent}% del objetivo ({consumed}/{target} kcal)
      </p>
      <div className="flex flex-wrap gap-2 text-sm">
        <Link
          to="/nutrition/today"
          className="flex h-10 items-center gap-1 rounded bg-blue-500 px-4 text-white"
        >
          <PlusCircle className="h-4 w-4" /> Añadir comida
        </Link>
        <Link
          to="/nutrition/plan"
          className="flex h-10 items-center gap-1 rounded border px-4"
        >
          <CalendarDays className="h-4 w-4" /> Ver semana
        </Link>
        <Link
          to="/shopping-list"
          className="flex h-10 items-center gap-1 rounded border px-4"
        >
          <ShoppingCart className="h-4 w-4" /> Lista de compra
        </Link>
      </div>
    </section>
  );
}
