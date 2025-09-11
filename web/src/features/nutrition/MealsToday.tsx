import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  getDayLog,
  createMeal,
  deleteMeal,
  deleteMealItem,
  updateMeal,
  updateMealItem,
  addMealItemFlexible,
  type Meal,
} from '../../api/nutrition';
import { today } from '../../utils/date';
import FoodPicker from '../../components/FoodPicker';

export default function MealsToday() {
  const date = today();
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ['nutrition-day', date], queryFn: () => getDayLog(date) });

  const createDefaults = useMutation({
    mutationFn: async () => {
      await Promise.all([
        createMeal({ date, meal_type: 'breakfast', name: 'Desayuno' }),
        createMeal({ date, meal_type: 'lunch', name: 'Comida' }),
        createMeal({ date, meal_type: 'dinner', name: 'Cena' }),
      ]);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  const addItemFlexible = useMutation({
    mutationFn: ({ mealId, payload }: { mealId: string; payload: any }) =>
      addMealItemFlexible(mealId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  if (!data) return <p>Cargando...</p>;
  if (data.meals.length === 0) {
    return (
      <div className="space-y-2 p-3">
        <p>No hay comidas registradas</p>
        <p className="text-sm text-gray-600">Crea estructura básica para hoy o ve al plan semanal.</p>
        <div className="flex gap-2">
          <button
            className="inline-block rounded border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
            onClick={() => createDefaults.mutate()}
          >
            Crear Desayuno/Comida/Cena
          </button>
          <Link
            to="/nutrition/plan"
            role="button"
            aria-label="Plan semanal"
            tabIndex={0}
            className="inline-block rounded border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            Ir al plan semanal
          </Link>
        </div>
      </div>
    );
  }

  const consumed = data.totals?.calories_kcal ?? 0;
  const progress = data.targets?.calories_target
    ? Math.min(100, Math.round((consumed / data.targets.calories_target) * 100))
    : 0;

  return (
    <div className="space-y-3 p-3 text-sm">
      <div>
        <div className="mb-2">Adherencia: {progress}%</div>
        <div className="h-2 w-full bg-gray-200">
          <div className="h-2 bg-green-500" style={{ width: `${progress}%` }} />
        </div>
      </div>
      {data.meals.map((meal: Meal) => (
        <div key={meal.id} className="space-y-2 rounded border p-3">
          <div className="flex justify-between">
            <h3 className="font-semibold">{meal.name || meal.meal_type}</h3>
            <div className="space-x-2 text-sm">
              <button
                className="h-8 px-2"
                onClick={() => {
                  const name = prompt('Nuevo nombre', meal.name);
                  if (name) updateMeal(meal.id, { name }).then(() =>
                    qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                  );
                }}
              >
                Editar
              </button>
              <button
                className="h-8 px-2"
                onClick={() => deleteMeal(meal.id).then(() =>
                  qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                )}
              >
                Borrar
              </button>
            </div>
          </div>
          <ul className="space-y-1">
            {meal.items.map((item) => (
              <li key={item.id} className="flex justify-between">
                <span>
                  {item.food_name} ({item.serving_qty} {item.serving_unit}) - {Number(item.calories_kcal)} kcal
                </span>
                <div className="space-x-1 text-sm">
                  <button
                    className="h-8 px-2"
                    onClick={() => {
                      const qtyRaw = prompt('Cantidad (actual)', String(item.serving_qty));
                      const qty = qtyRaw ? Number(qtyRaw) : undefined;
                      if (qty == null || Number.isNaN(qty)) return;
                      updateMealItem(meal.id, item.id, { serving_qty: qty }).then(() =>
                        qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                      );
                    }}
                  >
                    Editar
                  </button>
                  <button
                    className="h-8 px-2"
                    onClick={() =>
                      deleteMealItem(meal.id, item.id).then(() =>
                        qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                      )
                    }
                  >
                    Borrar
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-3">
            <FoodPicker
              mealId={meal.id}
              onAdded={() => qc.invalidateQueries({ queryKey: ['nutrition-day', date] })}
              onManual={(prefill) => {
                const name = prefill?.name ?? prompt('Nombre del alimento') ?? '';
                if (!name) return;
                const unitRaw = prompt('Unidad (g/ml/unidad)', 'g') || 'g';
                const qty = Number(prompt('Cantidad', '100') || '100');
                const kcal = Number(prompt('kcal', '0') || '0');
                const p = Number(prompt('Proteína (g)', '0') || '0');
                const c = Number(prompt('Carbohidratos (g)', '0') || '0');
                const f = Number(prompt('Grasa (g)', '0') || '0');
                addItemFlexible.mutate({
                  mealId: meal.id,
                  payload: {
                    food_name: name,
                    serving_qty: qty,
                    serving_unit: unitRaw === 'unidad' ? 'unidad' : (unitRaw as any),
                    calories_kcal: kcal,
                    protein_g: p,
                    carbs_g: c,
                    fat_g: f,
                  },
                });
              }}
            />
          </div>
        </div>
      ))}
      <div className="pt-2">
        <Link
          to="/nutrition/plan"
          role="button"
          aria-label="Editar en plan semanal"
          className="inline-block h-10 rounded border px-4 align-middle leading-10 focus:outline-none focus:ring-2 focus:ring-sky-400"
        >
          Editar en plan semanal
        </Link>
      </div>
    </div>
  );
}
