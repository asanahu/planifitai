import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import {
  getDayLog,
  createMeal,
  deleteMeal,
  deleteMealItem,
  updateMealItem,
  addMealItemFlexible,
  type Meal,
} from '../../api/nutrition';
import { today } from '../../utils/date';
import { getMealPlanForWeek, setMealPlanForWeek } from '../../utils/storage';
import { useAutoSyncMeals } from '../../hooks/useAutoSyncMeals';
import FoodPicker from '../../components/FoodPicker';
import CaloriesDisplay from '../../components/CaloriesDisplay';
import { Plus, Edit3, Trash2, Target, AlertCircle, Utensils, Coffee, Sun, Moon, Apple, Calendar } from 'lucide-react';
import Button from '../../components/ui/button';
import Card from '../../components/ui/card';

const mealTypeNames: Record<string, string> = {
  breakfast: 'Desayuno',
  lunch: 'Comida',
  dinner: 'Cena',
  snack: 'Merienda',
  other: 'Otro',
};

const englishToSpanishNames: Record<string, string> = {
  Breakfast: 'Desayuno',
  Lunch: 'Comida',
  Dinner: 'Cena',
  Snack: 'Merienda',
  Other: 'Otro',
};

const mealIcons: Record<string, React.ReactNode> = {
  breakfast: <Coffee className="h-5 w-5 text-orange-500" />,
  lunch: <Sun className="h-5 w-5 text-yellow-500" />,
  dinner: <Moon className="h-5 w-5 text-blue-500" />,
  snack: <Apple className="h-5 w-5 text-green-500" />,
  other: <Utensils className="h-5 w-5 text-gray-500" />,
};

const mealColors: Record<string, string> = {
  breakfast: 'orange',
  lunch: 'yellow',
  dinner: 'blue',
  snack: 'green',
  other: 'gray',
};

function formatYMDLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getWeekDates(weekKey: string): string[] {
  const now = new Date();
  const currentDay = now.getDay();
  const mondayOffset = currentDay === 0 ? -6 : 1 - currentDay;
  const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  monday.setDate(monday.getDate() + mondayOffset + (weekKey === 'week2' ? 7 : 0));
  const dates: string[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate());
    d.setDate(monday.getDate() + i);
    dates.push(formatYMDLocal(d));
  }
  return dates;
}

export default function MealsToday({ onDateChange }: { onDateChange?: (dayName: string) => void }) {
  const [searchParams] = useSearchParams();
  const dayParam = searchParams.get('day');
  const weekParam = searchParams.get('week') || 'week1';
  const [mode, setMode] = React.useState<'consumed' | 'planned'>('consumed');
  const { syncCurrentDay, syncIndividualFood } = useAutoSyncMeals();

  const dayMap: Record<string, number> = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 };
  const getDateFromDay = (dayKey: string) => {
    const weekDates = getWeekDates(weekParam);
    const dayIndex = dayMap[dayKey] ?? 0;
    return weekDates[dayIndex];
  };

  const date = dayParam ? getDateFromDay(dayParam) : today();
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ['nutrition-day', date], queryFn: () => getDayLog(date) });

  const isEditingToday = date === today();
  const actualDayName = isEditingToday ? 'hoy' : new Date(date).toLocaleDateString('es-ES', { weekday: 'long' });

  React.useEffect(() => {
    onDateChange?.(actualDayName);
  }, [actualDayName, onDateChange]);

  const createDefaults = useMutation({
    mutationFn: async () => {
      await Promise.all([
        createMeal({ date, meal_type: 'breakfast', name: 'Desayuno' }),
        createMeal({ date, meal_type: 'lunch', name: 'Comida' }),
        createMeal({ date, meal_type: 'dinner', name: 'Cena' }),
        createMeal({ date, meal_type: 'snack', name: 'Merienda' }),
      ]);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  const addItemFlexible = useMutation({
    mutationFn: ({ mealId, payload }: { mealId: string; payload: any }) => addMealItemFlexible(mealId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  const cleanupDuplicates = useMutation({
    mutationFn: async () => {
      if (!data) return;
      const mealTypes = new Set<string>();
      const mealsToDelete: number[] = [];
      data.meals.forEach((meal) => {
        if (mealTypes.has(meal.meal_type)) mealsToDelete.push(meal.id);
        else mealTypes.add(meal.meal_type);
      });
      await Promise.all(mealsToDelete.map((mealId) => deleteMeal(mealId)));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  // Planned view state
  const dayKeyForDate = React.useMemo(() => {
    const d = new Date(date);
    const map: Record<number, string> = { 0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat' };
    return map[d.getDay()] || 'Mon';
  }, [date]);

  const [plannedLocal, setPlannedLocal] = React.useState<Record<string, string[]>>({});

  React.useEffect(() => {
    const weekly = getMealPlanForWeek(weekParam);
    const key = dayParam || dayKeyForDate;
    setPlannedLocal((weekly as any)[key] || {});
  }, [weekParam, dayParam, dayKeyForDate]);

  const updatePlanned = (updater: (prev: Record<string, string[]>) => Record<string, string[]>) => {
    const next = updater(plannedLocal);
    setPlannedLocal(next);
    const weekly = getMealPlanForWeek(weekParam);
    const key = dayParam || dayKeyForDate;
    const updated = { ...(weekly as any), [key]: next } as any;
    setMealPlanForWeek(weekParam as any, updated);
    try {
      window.dispatchEvent(new Event('mealplan:updated'));
    } catch {}
  };

  const importPlannedDay = useMutation({
    mutationFn: async () => {
      await syncCurrentDay(date);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Cargando comidas del día...</p>
        </div>
      </div>
    );
  }

  const normalizedMeals = data.meals.reduce((acc: Meal[], meal: Meal) => {
    const normalizedName = meal.name ? englishToSpanishNames[meal.name] || meal.name : mealTypeNames[meal.meal_type] || meal.meal_type;
    const mealKey = `${meal.meal_type}_${normalizedName.toLowerCase()}`;
    const existingIndex = acc.findIndex((m) => {
      const existingKey = `${m.meal_type}_${(m.name || mealTypeNames[m.meal_type] || '').toLowerCase()}`;
      return existingKey === mealKey || m.meal_type === meal.meal_type;
    });
    if (existingIndex >= 0) {
      const existingMeal = acc[existingIndex];
      const newItems = meal.items.filter(
        (ni) => !existingMeal.items.some((ei) => ei.food_name === ni.food_name && ei.serving_qty === ni.serving_qty && ei.serving_unit === ni.serving_unit)
      );
      existingMeal.items = [...existingMeal.items, ...newItems];
    } else {
      acc.push({ ...meal, name: normalizedName });
    }
    return acc;
  }, [] as Meal[]);

  const consumed = Number(data.totals?.calories_kcal) || 0;
  const target = data.targets?.calories_target ?? 2000;
  const progress = Math.min(100, Math.round((consumed / target) * 100));

  return (
    <div className="space-y-6 p-6">
      {/* Progress & controls */}
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <Target className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Progreso del día</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Adherencia: {progress}%</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button onClick={() => setMode('consumed')} className={`px-3 py-1 text-sm rounded ${mode === 'consumed' ? 'bg-white dark:bg-gray-600 text-blue-600' : 'text-gray-600 dark:text-gray-300'}`}>
                Consumido
              </button>
              <button onClick={() => setMode('planned')} className={`px-3 py-1 text-sm rounded ${mode === 'planned' ? 'bg-white dark:bg-gray-600 text-blue-600' : 'text-gray-600 dark:text-gray-300'}`}>
                Planificado
              </button>
            </div>
            {data.meals.length > normalizedMeals.length && (
              <Button variant="secondary" onClick={() => cleanupDuplicates.mutate()} disabled={cleanupDuplicates.isPending} className="gap-2 text-orange-600 border-orange-200 hover:bg-orange-50">
                <AlertCircle className="h-4 w-4" /> {cleanupDuplicates.isPending ? 'Limpiando...' : 'Limpiar duplicados'}
              </Button>
            )}
            <Button variant="secondary" onClick={() => importPlannedDay.mutate()} disabled={importPlannedDay.isPending} className="gap-2">
              <Calendar className="h-4 w-4" /> {importPlannedDay.isPending ? 'Importando...' : 'Importar plan del día'}
            </Button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>Consumido</span>
            <span className="flex items-center gap-1">
              <CaloriesDisplay calories={consumed} />
              <span>/ {target} kcal</span>
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
            <div className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              <CaloriesDisplay calories={Math.round(consumed)} />
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Consumido</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">{target}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Objetivo</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{normalizedMeals.length}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Comidas</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {normalizedMeals.reduce((total, meal) => total + meal.items.length, 0)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Alimentos</div>
          </div>
        </div>
      </Card>

      {/* Meals / Plan */}
      {mode === 'consumed' ? (
        <div className="space-y-6">
          {normalizedMeals.map((meal: Meal) => {
            const mealColor = mealColors[meal.meal_type] || 'gray';
            const mealIcon = mealIcons[meal.meal_type] || <Utensils className="h-5 w-5" />;
            const mealCalories = meal.items.reduce((sum, item) => sum + (Number(item.calories_kcal) || 0), 0);
            return (
              <Card key={meal.id} className="overflow-hidden">
                <div className={`bg-gradient-to-r from-${mealColor}-50 to-${mealColor}-100 dark:from-${mealColor}-900/20 dark:to-${mealColor}-800/20 p-4 border-b border-${mealColor}-200 dark:border-${mealColor}-700`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 bg-${mealColor}-100 dark:bg-${mealColor}-900/30 rounded-lg`}>{mealIcon}</div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{meal.name || meal.meal_type}</h3>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <CaloriesDisplay calories={Math.round(mealCalories)} />
                          <span>kcal</span>
                          <span>•</span>
                          <span>{meal.items.length} alimentos</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-4">
                  {meal.items.length > 0 ? (
                    <div className="space-y-3 mb-4">
                      {meal.items.map((item) => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 dark:text-white">{item.food_name}</div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">{item.serving_qty} {item.serving_unit}</div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <div className="font-semibold text-gray-900 dark:text-white">
                                <CaloriesDisplay calories={Math.round(Number(item.calories_kcal) || 0)} />
                              </div>
                              <div className="text-xs text-gray-500">kcal</div>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="secondary"
                                onClick={() => {
                                  const qtyRaw = prompt('Cantidad (actual)', String(item.serving_qty));
                                  const qty = qtyRaw ? Number(qtyRaw) : undefined;
                                  if (qty == null || Number.isNaN(qty)) return;
                                  updateMealItem(meal.id, item.id, { serving_qty: qty }).then(() =>
                                    qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                                  );
                                }}
                                className="h-8 w-8 p-0"
                              >
                                <Edit3 className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="secondary"
                                onClick={() => deleteMealItem(meal.id, item.id).then(() => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }))}
                                className="h-8 w-8 p-0 text-red-600 border-red-200 hover:bg-red-50"
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Utensils className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No hay alimentos registrados</p>
                    </div>
                  )}
                  <div className="border-top border-gray-200 dark:border-gray-700 pt-4">
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
                          mealId: String(meal.id),
                          payload: { food_name: name, serving_qty: qty, serving_unit: unitRaw === 'unidad' ? 'unidad' : (unitRaw as any), calories_kcal: kcal, protein_g: p, carbs_g: c, fat_g: f },
                        });
                      }}
                      useSmartSearch={true}
                      searchContext={mealTypeNames[meal.meal_type]}
                    />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="space-y-6">
          {['Breakfast', 'Lunch', 'Dinner', 'Snack'].map((planMeal) => {
            const plannedItems = (plannedLocal as any)[planMeal] || ([] as string[]);
            const backendTypeMap: Record<string, string> = { Breakfast: 'breakfast', Lunch: 'lunch', Dinner: 'dinner', Snack: 'snack' };
            const titleMap: Record<string, string> = { Breakfast: 'Desayuno', Lunch: 'Comida', Dinner: 'Cena', Snack: 'Merienda' };
            const colorMap: Record<string, string> = { Breakfast: 'orange', Lunch: 'yellow', Dinner: 'blue', Snack: 'green' };
            const iconMap: Record<string, JSX.Element> = {
              Breakfast: <Coffee className="h-5 w-5 text-orange-500" />,
              Lunch: <Sun className="h-5 w-5 text-yellow-500" />,
              Dinner: <Moon className="h-5 w-5 text-blue-500" />,
              Snack: <Apple className="h-5 w-5 text-green-500" />,
            };
            const color = colorMap[planMeal] || 'gray';
            return (
              <Card key={planMeal} className={`overflow-hidden border-l-4 border-${color}-400`}> 
                <div className="p-4 border-b flex items-center justify-between bg-white dark:bg-gray-900">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-${color}-100 dark:bg-${color}-900/30`}>{iconMap[planMeal]}</div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{titleMap[planMeal]}</h3>
                      <div className="text-xs text-gray-500">{plannedItems.length} alimentos planificados</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      onClick={async () => {
                        // Copiar toda la comida a consumido
                        for (const food of plannedItems) {
                          await syncIndividualFood(backendTypeMap[planMeal], food, date);
                        }
                      }}
                      className={`h-8 px-2 text-${color}-700 border-${color}-200 hover:bg-${color}-50`}
                    >
                      <Utensils className="h-4 w-4 mr-1" /> Copiar todo
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        const name = prompt('Añadir alimento al plan (nombre)')?.trim();
                        if (!name) return;
                        updatePlanned((prev) => {
                          const next = { ...prev } as any;
                          if (!next[planMeal]) next[planMeal] = [];
                          next[planMeal] = [...next[planMeal], name];
                          return next;
                        });
                      }}
                      className="h-8 gap-2"
                    >
                      <Plus className="h-4 w-4" /> Añadir
                    </Button>
                  </div>
                </div>
                <div className="p-4">
                  {plannedItems.length === 0 ? (
                    <p className="text-sm text-gray-500">Sin alimentos planificados</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {plannedItems.map((food, idx) => (
                        <div key={idx} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700">
                          <span className="text-sm">{food}</span>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="secondary"
                              onClick={async () => { await syncIndividualFood(backendTypeMap[planMeal], food, date); }}
                              className={`h-7 px-2 text-${color}-700 border-${color}-200 hover:bg-${color}-50`}
                            >
                              <Utensils className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="secondary"
                              onClick={() => {
                                updatePlanned((prev) => {
                                  const next = { ...prev } as any;
                                  next[planMeal] = (next[planMeal] || []).filter((x: string, i: number) => i !== idx);
                                  return next;
                                });
                              }}
                              className="h-7 px-2 text-red-600 border-red-200 hover:bg-red-50"
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

