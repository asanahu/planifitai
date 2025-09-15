import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/ui/button';
import {
  ClipboardCheck,
  Eraser,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Utensils,
  Calendar,
  Settings,
  CheckCircle,
  AlertCircle,
  Target,
  TrendingUp,
} from 'lucide-react';
import {
  getMealPlanForWeek,
  setMealPlanForWeek,
  getMealActualsForWeek,
  setMealActualsForWeek,
} from '../../utils/storage';
import { useAutoSyncMeals } from '../../hooks/useAutoSyncMeals';
import { getDayLog, createMeal, deleteMealItem } from '../../api/nutrition';
import type { MealPlan } from '../../utils/storage';
import { calculateFoodCalories, clearGlobalCaloriesCache } from '../../utils/caloriesCalculator';
import CaloriesDisplay from '../../components/CaloriesDisplay';
import GeneratePlanFromAI from './GeneratePlanFromAI';

const dayKeys = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
type DayKey = (typeof dayKeys)[number];
const dayLabels: Record<DayKey, string> = {
  Mon: 'Lunes',
  Tue: 'Martes',
  Wed: 'Miércoles',
  Thu: 'Jueves',
  Fri: 'Viernes',
  Sat: 'Sábado',
  Sun: 'Domingo',
};
const weekKeys = ['week1', 'week2'] as const;
type WeekKey = (typeof weekKeys)[number];
const weekLabels: Record<WeekKey, string> = {
  week1: 'Semana 1',
  week2: 'Semana 2',
};

function formatYMDLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
function parseYMDLocal(s: string): Date {
  const [y, m, d] = s.split('-').map((n) => Number(n));
  return new Date(y, (m || 1) - 1, d || 1);
}

function getWeekDates(weekKey: WeekKey): { start: string; end: string; dates: string[] } {
  const todayLocal = new Date();
  const currentDay = todayLocal.getDay();
  const mondayOffset = currentDay === 0 ? -6 : 1 - currentDay;
  const mondayOfCurrentWeek = new Date(todayLocal.getFullYear(), todayLocal.getMonth(), todayLocal.getDate());
  mondayOfCurrentWeek.setDate(mondayOfCurrentWeek.getDate() + mondayOffset);

  const weekOffset = weekKey === 'week1' ? 0 : 7;
  const targetMonday = new Date(mondayOfCurrentWeek.getFullYear(), mondayOfCurrentWeek.getMonth(), mondayOfCurrentWeek.getDate());
  targetMonday.setDate(targetMonday.getDate() + weekOffset);

  const dates: string[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(targetMonday.getFullYear(), targetMonday.getMonth(), targetMonday.getDate());
    d.setDate(targetMonday.getDate() + i);
    dates.push(formatYMDLocal(d));
  }
  return { start: dates[0], end: dates[6], dates };
}

function getDateFromDayAndWeek(dayKey: DayKey, weekKey: WeekKey): string {
  const weekDates = getWeekDates(weekKey);
  const dayIndex = dayKeys.indexOf(dayKey);
  return weekDates.dates[dayIndex];
}

function getDayWithDate(dayKey: DayKey, weekKey: WeekKey): string {
  const date = getDateFromDayAndWeek(dayKey, weekKey);
  const dayDate = parseYMDLocal(date);
  const dayNumber = dayDate.getDate();
  return `${dayLabels[dayKey]} ${dayNumber}`;
}

const mealKeys = ['Breakfast', 'Lunch', 'Dinner', 'Snack'] as const;
const mealLabels: Record<(typeof mealKeys)[number], string> = {
  Breakfast: 'Desayuno',
  Lunch: 'Comida',
  Dinner: 'Cena',
  Snack: 'Merienda',
};

function currentDayKey(): DayKey {
  const d = new Date().getDay();
  const map: Record<number, DayKey> = { 0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat' };
  return map[d] ?? 'Mon';
}

export default function MealsPlan() {
  const [selectedWeek, setSelectedWeek] = useState<WeekKey>('week1');
  const [view, setView] = useState<'day' | 'week'>('day');
  const [selectedDay, setSelectedDay] = useState<DayKey>(() => currentDayKey());
  const [caloriesData, setCaloriesData] = useState<{
    planned: number;
    real: number;
    target: number;
    plannedPercentage: number;
    realPercentage: number;
  } | null>(null);
  const [isLoadingCalories, setIsLoadingCalories] = useState(false);
  const { syncCurrentDay } = useAutoSyncMeals();

  const [currentWeekPlan, setCurrentWeekPlan] = useState<MealPlan>(() => getMealPlanForWeek(selectedWeek));
  const [currentWeekActuals, setCurrentWeekActuals] = useState<Record<string, Record<string, string[]>>>(
    () => getMealActualsForWeek(selectedWeek)
  );

  useEffect(() => {
    setCurrentWeekPlan(getMealPlanForWeek(selectedWeek));
    setCurrentWeekActuals(getMealActualsForWeek(selectedWeek));
  }, [selectedWeek]);

  useEffect(() => {
    const handler = () => setCurrentWeekPlan(getMealPlanForWeek(selectedWeek));
    window.addEventListener('mealplan:updated', handler);
    return () => window.removeEventListener('mealplan:updated', handler);
  }, [selectedWeek]);

  const setPlan = (p: MealPlan) => {
    setMealPlanForWeek(selectedWeek, p);
    setCurrentWeekPlan(p);
  };
  const setActuals = (a: Record<string, Record<string, string[]>>) => {
    setMealActualsForWeek(selectedWeek, a);
    setCurrentWeekActuals(a);
  };

  const copyDay = (from: string, to: string) => {
    const next = { ...currentWeekPlan, [to]: { ...currentWeekPlan[from] } };
    setPlan(next);
    const nextA = { ...currentWeekActuals, [to]: { ...(currentWeekActuals as any)[from] } } as any;
    setActuals(nextA);
  };

  const clearDayPlanned = (day: string) => {
    if (!confirm('Vas a borrar el planificado de este día. ¿Continuar?')) return;
    const next = { ...currentWeekPlan } as any;
    delete next[day];
    setPlan(next);
  };

  const ensureMealStructure = async (date: string) => {
    try {
      const todayStr = formatYMDLocal(new Date());
      if (date > todayStr) return;
      const dayLog = await getDayLog(date);
      const existingMealTypes = new Set(dayLog.meals.map((m) => m.meal_type));
      const requiredMealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];
      const missing = requiredMealTypes.filter((t) => !existingMealTypes.has(t as any));
      for (const mealType of missing) {
        const mealNames = { breakfast: 'Desayuno', lunch: 'Comida', dinner: 'Cena', snack: 'Merienda' } as const;
        await createMeal({
          date,
          meal_type: mealType as 'breakfast' | 'lunch' | 'dinner' | 'snack',
          name: mealNames[mealType as keyof typeof mealNames],
        });
      }
    } catch (error) {
      console.error('❌ Error creando estructura de comidas:', error);
    }
  };

  const clearDayActual = async (day: DayKey) => {
    if (!confirm('Vas a borrar los alimentos de este día (manteniendo la estructura). ¿Continuar?')) return;
    try {
      const date = getDateFromDayAndWeek(day, selectedWeek);
      await ensureMealStructure(date);
      const dayLog = await getDayLog(date);
      for (const meal of dayLog.meals) {
        for (const item of meal.items) {
          await deleteMealItem(meal.id, item.id);
        }
      }
      const nextA = { ...currentWeekActuals } as any;
      delete nextA[day];
      setActuals(nextA);
    } catch (error) {
      console.error('❌ Error eliminando alimentos:', error);
      alert('Error al eliminar los alimentos. Inténtalo de nuevo.');
    }
  };

    const copyPlanToActual = async (day: string) => {
    const mealsPlan = currentWeekPlan[day] || {};
    const next = { ...currentWeekActuals } as any;
    next[day] = Object.fromEntries(
      Object.entries(mealsPlan).map(([meal, items]) => [meal, [...(items as string[])]])
    );
    setActuals(next);
    // Sincronizar el día concreto (sea hoy u otro día)
    const date = getDateFromDayAndWeek(day as DayKey, selectedWeek);
    await syncCurrentDay(date);
  };const copyTwoWeeksPlanToActuals = async () => {
    const nextWeek1 = { ...getMealActualsForWeek('week1') } as any;
    const nextWeek2 = { ...getMealActualsForWeek('week2') } as any;
    const week1Plan = getMealPlanForWeek('week1');
    const week2Plan = getMealPlanForWeek('week2');
    Object.entries(week1Plan).forEach(([d, meals]) => {
      nextWeek1[d] = Object.fromEntries(
        Object.entries(meals as any).map(([meal, items]) => [meal, [...(items as string[])]])
      );
    });
    Object.entries(week2Plan).forEach(([d, meals]) => {
      nextWeek2[d] = Object.fromEntries(
        Object.entries(meals as any).map(([meal, items]) => [meal, [...(items as string[])]])
      );
    });
    setMealActualsForWeek('week1', nextWeek1);
    setMealActualsForWeek('week2', nextWeek2);
    await syncCurrentDay();
  };

  const clearWeekPlanned = () => {
    if (!confirm('Vas a borrar TODO el plan semanal. ¿Continuar?')) return;
    setPlan({});
  };

  const clearWeekActuals = async () => {
    if (!confirm('Vas a borrar TODOS los alimentos de la semana seleccionada (manteniendo la estructura). ¿Continuar?'))
      return;
    try {
      for (const day of dayKeys) {
        const date = getDateFromDayAndWeek(day, selectedWeek);
        try {
          await ensureMealStructure(date);
          const dayLog = await getDayLog(date);
          for (const meal of dayLog.meals) {
            for (const item of meal.items) {
              await deleteMealItem(meal.id, item.id);
            }
          }
        } catch {
          // Ignorar días sin comidas
        }
      }
      const nextA = { ...currentWeekActuals } as any;
      for (const day of dayKeys) delete nextA[day];
      setActuals(nextA);
    } catch (error) {
      console.error('❌ Error eliminando alimentos de la semana:', error);
      alert('Error al eliminar los alimentos. Inténtalo de nuevo.');
    }
  };

  const clearTwoWeeksPlanned = () => {
    if (!confirm('Vas a borrar TODO el plan de las 2 semanas. ¿Continuar?')) return;
    setMealPlanForWeek('week1', {});
    setMealPlanForWeek('week2', {});
    if (selectedWeek === 'week1' || selectedWeek === 'week2') setCurrentWeekPlan({});
  };

  const clearTwoWeeksActuals = async () => {
    if (!confirm('Vas a borrar TODOS los alimentos de las 2 semanas (manteniendo la estructura). ¿Continuar?'))
      return;
    try {
      for (const w of weekKeys) {
        for (const day of dayKeys) {
          const date = getDateFromDayAndWeek(day, w);
          try {
            await ensureMealStructure(date);
            const dayLog = await getDayLog(date);
            for (const meal of dayLog.meals) {
              for (const item of meal.items) {
                await deleteMealItem(meal.id, item.id);
              }
            }
          } catch {
            // Ignorar días sin comidas
          }
        }
      }
      setMealActualsForWeek('week1', {});
      setMealActualsForWeek('week2', {});
      setCurrentWeekActuals({});
    } catch (error) {
      console.error('❌ Error eliminando alimentos de 2 semanas:', error);
      alert('Error al eliminar los alimentos. Inténtalo de nuevo.');
    }
  };

  // Inicializar estructura básica en días <= hoy
  useEffect(() => {
    const initializeMealStructures = async () => {
      const todayStr = formatYMDLocal(new Date());
      for (const week of weekKeys) {
        for (const day of dayKeys) {
          const date = getDateFromDayAndWeek(day, week);
          if (date <= todayStr) await ensureMealStructure(date);
        }
      }
    };
    initializeMealStructures();
  }, []);

  const DayCard = ({ day }: { day: DayKey }) => {
    const plannedCount = mealKeys.reduce((acc, mk) => acc + ((currentWeekPlan[day]?.[mk] || []).length), 0);
    const eatenCount = mealKeys.reduce(
      (acc, mk) => acc + ((((currentWeekActuals as any)[day]?.[mk]) || []).length),
      0
    );
    const hasPlan = plannedCount > 0;
    const hasEaten = eatenCount > 0;

    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg border shadow-sm">
        {/* Header del día */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-gray-500" />
            <h3 className="text-lg font-semibold">{getDayWithDate(day, selectedWeek)}</h3>
            {hasPlan && <CheckCircle className="h-4 w-4 text-green-500" />}
            {!hasPlan && <AlertCircle className="h-4 w-4 text-gray-400" />}
          </div>

          {/* Acciones principales del día */}
          <div className="flex items-center gap-2">
            {hasPlan && (
              <Button
                variant="secondary"
                onClick={() => copyPlanToActual(day)}
                className="text-green-600 border-green-200 hover:bg-green-50"
              >
                <ClipboardCheck className="h-4 w-4 mr-1" />
                Copiar plan a comidas reales
              </Button>
            )}
            {view === 'day' && (
              <Button
                variant="secondary"
                onClick={() => clearDayActual(day)}
                className="text-red-600 border-red-200 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Limpiar datos del día
              </Button>
            )}
            <Link to={`/nutrition/today?day=${day}&week=${selectedWeek}`}>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Utensils className="h-4 w-4 mr-1" />
                Editar
              </Button>
            </Link>
          </div>
        </div>

        {/* Contenido del día */}
        <div className="p-4">
          {/* Resumen */}
          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Resumen del día:</span>
              <div className="flex gap-4">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  Planificados: {plannedCount}
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  Consumidos: {eatenCount}
                </span>
              </div>
            </div>
          </div>

          {/* Comidas */}
          <div className="space-y-3">
            {mealKeys.map((meal) => {
              const planned = currentWeekPlan[day]?.[meal] || [];
              const eaten = (currentWeekActuals as any)[day]?.[meal] || [];
              const hasPlanned = planned.length > 0;
              const hasEaten = eaten.length > 0;
              return (
                <div key={meal} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">{mealLabels[meal]}</h4>
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      {hasPlanned && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">Planificado</span>
                      )}
                      {hasEaten && (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded">Consumido</span>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2">
                    {/* Planificado */}
                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Planificado</div>
                      <div className="min-h-[40px] p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200">
                        {hasPlanned ? (
                          <ul className="space-y-1">
                            {planned.map((item, index) => (
                              <li key={index} className="text-sm text-gray-700 dark:text-gray-300">• {item}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-gray-400 italic">Sin planificar</p>
                        )}
                      </div>
                    </div>

                    {/* Consumido */}
                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Consumido</div>
                      <div className="min-h-[40px] p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200">
                        {hasEaten ? (
                          <ul className="space-y-1">
                            {eaten.map((item: string, index: number) => (
                              <li key={index} className="text-sm text-gray-700 dark:text-gray-300">• {item}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-gray-400 italic">Sin registrar</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const clearCaloriesCache = () => clearGlobalCaloriesCache();

  const calculateCaloriesForDay = useCallback(
    async (day: DayKey) => {
      setIsLoadingCalories(true);
      try {
        const date = getDateFromDayAndWeek(day, selectedWeek);
        const dayLog = await getDayLog(date);
        const currentPlan = getMealPlanForWeek(selectedWeek);
        const plannedItems = currentPlan[day] || {};
        let plannedCalories = 0;
        const uniqueFoods = new Set<string>();
        Object.values(plannedItems).forEach((items: string[]) => {
          items.forEach((item) => {
            const cleanName = item.replace(/^\\d+[\\.,]?\\d*\\s*[a-zA-Z]*\\s*/, '').trim();
            uniqueFoods.add(cleanName);
          });
        });
        for (const foodName of uniqueFoods) {
          const result = await calculateFoodCalories(foodName);
          plannedCalories += result.calories;
        }
        const realCalories = dayLog?.totals?.calories_kcal || 0;
        const targetCalories = dayLog?.targets?.calories_target || 2000;
        setCaloriesData({
          planned: Math.round(plannedCalories),
          real: realCalories,
          target: targetCalories,
          plannedPercentage: targetCalories > 0 ? (plannedCalories / targetCalories) * 100 : 0,
          realPercentage: targetCalories > 0 ? (realCalories / targetCalories) * 100 : 0,
        });
      } catch (error) {
        console.error('Error calculando calorías:', error);
      } finally {
        setIsLoadingCalories(false);
      }
    },
    [selectedWeek]
  );

  useEffect(() => {
    if (view === 'day') {
      const timeoutId = setTimeout(() => {
        calculateCaloriesForDay(selectedDay);
      }, 300);
      return () => clearTimeout(timeoutId);
    }
  }, [selectedDay, selectedWeek, view, calculateCaloriesForDay]);

  useEffect(() => {
    if (view === 'day') {
      const timeoutId = setTimeout(() => {
        calculateCaloriesForDay(selectedDay);
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [currentWeekPlan, selectedDay, selectedWeek, view]);

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <GeneratePlanFromAI />
      </div>
      {/* Selector de semana */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="text-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Seleccionar Semana</h2>
          <div className="flex justify-center gap-4">
            {weekKeys.map((week) => {
              const weekDates = getWeekDates(week);
              const startDate = parseYMDLocal(weekDates.start).toLocaleDateString('es-ES', {
                day: 'numeric',
                month: 'short',
              });
              const endDate = parseYMDLocal(weekDates.end).toLocaleDateString('es-ES', {
                day: 'numeric',
                month: 'short',
              });
              return (
                <button
                  key={week}
                  onClick={() => setSelectedWeek(week)}
                  className={`px-6 py-3 rounded-lg border-2 transition-all duration-200 ${
                    selectedWeek === week
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                      : 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="text-sm font-medium">{weekLabels[week]}</div>
                  <div className="text-xs opacity-75">
                    {startDate} - {endDate}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Controles de vista y acciones */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
        <div className="flex flex-col items-center space-y-6">
          {/* Selector de vista */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Vista:</span>
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setView('day')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                  view === 'day'
                    ? 'bg-white dark:bg-gray-600 text-blue-600 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                Día
              </button>
              <button
                onClick={() => setView('week')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                  view === 'week'
                    ? 'bg-white dark:bg-gray-600 text-blue-600 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                Semana
              </button>
            </div>
          </div>

          {/* Acciones según vista */}

          {view === 'week' && (
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="text-sm text-gray-600 dark:text-gray-400">Acciones para 2 semanas</div>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  onClick={copyTwoWeeksPlanToActuals}
                  className="gap-2 text-green-600 border-green-200 hover:bg-green-50 dark:border-green-700 dark:hover:bg-green-900/20"
                >
                  <ClipboardCheck className="h-4 w-4" /> Copiar plan completo (2 semanas)
                </Button>
                <div className="relative group">
                  <Button variant="secondary" className="gap-2">
                    <Settings className="h-4 w-4" /> Limpiar datos (2 semanas)
                  </Button>
                  <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                    <div className="p-2">
                      <button
                        onClick={clearTwoWeeksPlanned}
                        className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                      >
                        <Eraser className="h-4 w-4 mr-2 inline" /> Limpiar plan (2 semanas)
                      </button>
                      <button
                        onClick={clearTwoWeeksActuals}
                        className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                      >
                        <Trash2 className="h-4 w-4 mr-2 inline" /> Limpiar comidas reales (2 semanas)
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navegación de días (solo en vista día) */}
      {view === 'day' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center justify-center gap-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-2">Día:</span>
            <Button
              variant="secondary"
              onClick={() => {
                const currentIndex = dayKeys.indexOf(selectedDay);
                const prevIndex = currentIndex > 0 ? currentIndex - 1 : dayKeys.length - 1;
                setSelectedDay(dayKeys[prevIndex]);
              }}
              className="flex-shrink-0"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            <div className="flex gap-1 overflow-x-auto">
              {dayKeys.map((d) => (
                <Button
                  key={d}
                  variant={selectedDay === d ? 'primary' : 'secondary'}
                  onClick={() => setSelectedDay(d)}
                  className="px-3 py-2 flex-shrink-0 text-sm font-medium"
                >
                  <span className="hidden sm:inline">{getDayWithDate(d, selectedWeek)}</span>
                  <span className="sm:hidden">{getDayWithDate(d, selectedWeek)}</span>
                </Button>
              ))}
            </div>

            <Button
              variant="secondary"
              onClick={() => {
                const currentIndex = dayKeys.indexOf(selectedDay);
                const nextIndex = currentIndex < dayKeys.length - 1 ? currentIndex + 1 : 0;
                setSelectedDay(dayKeys[nextIndex]);
              }}
              className="flex-shrink-0"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Contenido principal */}
      {view === 'week' && (
        <div className="space-y-4">
          {dayKeys.map((day) => (
            <DayCard key={day} day={day} />
          ))}
        </div>
      )}

      {view === 'day' && (
        <div className="max-w-4xl mx-auto space-y-6">
          <DayCard day={selectedDay} />

          {/* Comparación de Calorías */}
          {isLoadingCalories ? (
            <div className="bg-white dark:bg-gray-900 rounded-lg border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Target className="h-5 w-5 text-blue-500" />
                <h3 className="text-lg font-semibold">Comparación de Calorías</h3>
              </div>
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          ) : (
            caloriesData && (
              <div className="bg-white dark:bg-gray-900 rounded-lg border p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Target className="h-5 w-5 text-blue-500" />
                  <h3 className="text-lg font-semibold">
                    Comparación de Calorías - {getDayWithDate(selectedDay, selectedWeek)}
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  {/* Planificado */}
                  <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="flex items-center justify-center gap-1 mb-2">
                      <Target className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">Planificado</span>
                    </div>
                    <div className="text-2xl font-bold text-blue-600">
                      <CaloriesDisplay calories={caloriesData.planned} />
                    </div>
                    <div className="text-sm text-blue-600">kcal</div>
                    <div className="text-xs text-gray-600">{caloriesData.plannedPercentage.toFixed(0)}% del objetivo</div>
                  </div>

                  {/* Real */}
                  <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center justify-center gap-1 mb-2">
                      <Utensils className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium text-green-800">Consumido</span>
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                      <CaloriesDisplay calories={caloriesData.real} />
                    </div>
                    <div className="text-sm text-green-600">kcal</div>
                    <div className="text-xs text-gray-600">{caloriesData.realPercentage.toFixed(0)}% del objetivo</div>
                  </div>

                  {/* Diferencia */}
                  <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex items-center justify-center gap-1 mb-2">
                      <TrendingUp className="h-4 w-4 text-gray-600" />
                      <span className="text-sm font-medium text-gray-800">Diferencia</span>
                    </div>
                    <div
                      className={`text-2xl font-bold ${
                        caloriesData.real - caloriesData.planned > 100
                          ? 'text-red-600'
                          : caloriesData.real - caloriesData.planned < -100
                          ? 'text-blue-600'
                          : 'text-green-600'
                      }`}
                    >
                      {caloriesData.real - caloriesData.planned > 0 ? '+' : ''}
                      {caloriesData.real - caloriesData.planned}
                    </div>
                    <div className="text-sm text-gray-600">kcal</div>
                    <div className="text-xs text-gray-600">
                      {caloriesData.real - caloriesData.planned > 0
                        ? 'Más de lo planificado'
                        : caloriesData.real - caloriesData.planned < 0
                        ? 'Menos de lo planificado'
                        : 'Exacto'}
                    </div>
                  </div>
                </div>

                {/* Barras de progreso */}
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Planificado</span>
                      <span>{caloriesData.plannedPercentage.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${Math.min(caloriesData.plannedPercentage, 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Consumido</span>
                      <span>{caloriesData.realPercentage.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${Math.min(caloriesData.realPercentage, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Recalcular */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex justify-center">
                    <Button
                      variant="secondary"
                      onClick={clearCaloriesCache}
                      className="gap-2 text-blue-600 border-blue-200 hover:bg-blue-50 dark:border-blue-700 dark:hover:bg-blue-900/20"
                    >
                      <Target className="h-4 w-4" /> Recalcular calorías
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 text-center mt-2">
                    Limpia el caché y recalcula las calorías con los valores más actualizados
                  </p>
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}






