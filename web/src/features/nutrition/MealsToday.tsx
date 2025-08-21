import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDayLog,
  createMeal,
  createMealItem,
  deleteMeal,
  deleteMealItem,
  updateMeal,
  updateMealItem,
} from '../../api/nutrition';
import { today } from '../../utils/date';

export default function MealsToday() {
  const date = today();
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ['nutrition-day', date], queryFn: () => getDayLog(date) });

  const addMeal = useMutation({
    mutationFn: (name: string) => createMeal(date, { name }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  const addItem = useMutation({
    mutationFn: ({ mealId, name, quantity, unit, calories }: any) =>
      createMealItem(mealId, { name, quantity, unit, calories }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  if (!data) return <p>Cargando...</p>;

  const consumed = data.calories ?? data.totals?.calories ?? 0;
  const progress = data.targets?.calories
    ? Math.min(100, Math.round((consumed / data.targets.calories) * 100))
    : 0;

  return (
    <div className="space-y-3 p-3 text-sm">
      <div>
        <div className="mb-2">Adherencia: {progress}%</div>
        <div className="h-2 w-full bg-gray-200">
          <div className="h-2 bg-green-500" style={{ width: `${progress}%` }} />
        </div>
      </div>
      {data.meals.map((meal) => (
        <div key={meal.id} className="space-y-2 rounded border p-3">
          <div className="flex justify-between">
            <h3 className="font-semibold">{meal.name}</h3>
            <div className="space-x-2 text-sm">
              <button
                className="h-8 px-2"
                onClick={() => {
                  const name = prompt('Nuevo nombre', meal.name);
                  if (name) updateMeal(meal.id, { name }).then(() => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }));
                }}
              >
                Editar
              </button>
              <button
                className="h-8 px-2"
                onClick={() => deleteMeal(meal.id).then(() => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }))}
              >
                Borrar
              </button>
            </div>
          </div>
          <ul className="space-y-1">
            {meal.items.map((item) => (
              <li key={item.id} className="flex justify-between">
                <span>
                  {item.name} ({item.quantity} {item.unit}) - {item.calories} kcal
                </span>
                <div className="space-x-1 text-sm">
                  <button
                    className="h-8 px-2"
                    onClick={() => {
                      const name = prompt('Nombre', item.name);
                      if (!name) return;
                      updateMealItem(item.id, { name }).then(() => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }));
                    }}
                  >
                    Ed
                  </button>
                  <button
                    className="h-8 px-2"
                    onClick={() => deleteMealItem(item.id).then(() => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }))}
                  >
                    Del
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <button
            className="mt-2 h-8 text-blue-500"
            onClick={() => {
              const name = prompt('Item');
              if (!name) return;
              const quantity = Number(prompt('Cantidad') || '0');
              const unit = prompt('Unidad') || '';
              const calories = Number(prompt('kcal') || '0');
              addItem.mutate({ mealId: meal.id, name, quantity, unit, calories });
            }}
          >
            Añadir item
          </button>
        </div>
      ))}
      <button
        className="h-10 rounded bg-blue-500 px-4 text-white"
        onClick={() => {
          const name = prompt('Nombre de la comida');
          if (name) addMeal.mutate(name);
        }}
      >
        Añadir comida
      </button>
    </div>
  );
}
