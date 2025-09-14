import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
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
import CaloriesDisplay from '../../components/CaloriesDisplay';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  Target, 
  AlertCircle,
  Utensils,
  Coffee,
  Sun,
  Moon,
  Apple,
  Calendar
} from 'lucide-react';
import Button from '../../components/ui/button';
import Card from '../../components/ui/card';

// Mapeo de tipos de comida a nombres en español
const mealTypeNames: Record<string, string> = {
  'breakfast': 'Desayuno',
  'lunch': 'Comida',
  'dinner': 'Cena',
  'snack': 'Merienda',
  'other': 'Otro'
};

// Mapeo de nombres en inglés a español
const englishToSpanishNames: Record<string, string> = {
  'Breakfast': 'Desayuno',
  'Lunch': 'Comida',
  'Dinner': 'Cena',
  'Snack': 'Merienda',
  'Other': 'Otro'
};

// Comidas principales que no se pueden borrar ni editar el nombre
const mainMealTypes = ['breakfast', 'lunch', 'dinner', 'snack'];

// Iconos para cada tipo de comida
const mealIcons: Record<string, React.ReactNode> = {
  'breakfast': <Coffee className="h-5 w-5 text-orange-500" />,
  'lunch': <Sun className="h-5 w-5 text-yellow-500" />,
  'dinner': <Moon className="h-5 w-5 text-blue-500" />,
  'snack': <Apple className="h-5 w-5 text-green-500" />,
  'other': <Utensils className="h-5 w-5 text-gray-500" />
};

// Colores para cada tipo de comida
const mealColors: Record<string, string> = {
  'breakfast': 'orange',
  'lunch': 'yellow',
  'dinner': 'blue',
  'snack': 'green',
  'other': 'gray'
};

export default function MealsToday({ onDateChange }: { onDateChange?: (dayName: string) => void }) {
  const [searchParams] = useSearchParams();
  const dayParam = searchParams.get('day');
  const weekParam = searchParams.get('week') || 'week1'; // Nueva: obtener semana de la URL
  
  // Función para obtener las fechas de una semana específica
  const getWeekDates = (weekKey: string) => {
    const today = new Date();
    const currentDay = today.getDay(); // 0=Sun, 1=Mon, ..., 6=Sat
    
    // Calcular el lunes de la semana actual
    const mondayOffset = currentDay === 0 ? -6 : 1 - currentDay; // Si es domingo, ir al lunes anterior
    const mondayOfCurrentWeek = new Date(today);
    mondayOfCurrentWeek.setDate(today.getDate() + mondayOffset);
    
    // Calcular el lunes de la semana objetivo
    const weekOffset = weekKey === 'week1' ? 0 : 7;
    const targetMonday = new Date(mondayOfCurrentWeek);
    targetMonday.setDate(mondayOfCurrentWeek.getDate() + weekOffset);
    
    // Generar las 7 fechas de la semana
    const dates: string[] = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(targetMonday);
      date.setDate(targetMonday.getDate() + i);
      dates.push(date.toISOString().split('T')[0]);
    }
    
    return dates;
  };
  
  // Función para convertir día de la semana a fecha usando la semana seleccionada
  const getDateFromDay = (dayKey: string) => {
    const dayMap: Record<string, number> = { 'Sun': 0, 'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6 };
    const weekDates = getWeekDates(weekParam);
    const dayIndex = dayMap[dayKey] ?? 0;
    const calculatedDate = weekDates[dayIndex];
    
    // Verificar que la fecha no sea futura
    const today = new Date().toISOString().split('T')[0];
    if (calculatedDate > today) {
      console.log(`⚠️ Fecha futura detectada: ${calculatedDate}, usando fecha actual: ${today}`);
      return today;
    }
    
    return calculatedDate;
  };
  
  const date = dayParam ? getDateFromDay(dayParam) : today();
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ['nutrition-day', date], queryFn: () => getDayLog(date) });

  // Determinar si estamos editando hoy o un día pasado
  const isEditingToday = date === today();
  const actualDayName = isEditingToday ? 'hoy' : new Date(date).toLocaleDateString('es-ES', { weekday: 'long' });

  // Notificar al componente padre sobre la fecha actual
  React.useEffect(() => {
    if (onDateChange) {
      onDateChange(actualDayName);
    }
  }, [actualDayName, onDateChange]);

  // Las funciones de día ya no son necesarias aquí
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
    mutationFn: ({ mealId, payload }: { mealId: string; payload: any }) =>
      addMealItemFlexible(mealId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['nutrition-day', date] });
    },
  });

  // Función para limpiar comidas duplicadas
  const cleanupDuplicates = useMutation({
    mutationFn: async () => {
      if (!data) return;
      
      // Identificar comidas duplicadas (mismo tipo de comida)
      const mealTypes = new Set<string>();
      const mealsToDelete: number[] = [];
      
      data.meals.forEach(meal => {
        if (mealTypes.has(meal.meal_type)) {
          // Esta es una comida duplicada, marcar para eliminar
          mealsToDelete.push(meal.id);
        } else {
          mealTypes.add(meal.meal_type);
        }
      });
      
      // Eliminar comidas duplicadas
      await Promise.all(mealsToDelete.map(mealId => deleteMeal(mealId)));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition-day', date] }),
  });

  // El header ahora se maneja en NutritionTodayPage, no aquí

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
  
  // Filtrar y normalizar comidas para evitar duplicados
  const normalizedMeals = data.meals.reduce((acc: Meal[], meal: Meal) => {
    // Normalizar el nombre de la comida
    const normalizedName = meal.name ? 
      englishToSpanishNames[meal.name] || meal.name : 
      mealTypeNames[meal.meal_type] || meal.meal_type;
    
    // Crear una clave única para identificar comidas del mismo tipo
    const mealKey = `${meal.meal_type}_${normalizedName.toLowerCase()}`;
    
    // Buscar si ya existe una comida del mismo tipo
    const existingMealIndex = acc.findIndex(m => {
      const existingKey = `${m.meal_type}_${(m.name || mealTypeNames[m.meal_type] || '').toLowerCase()}`;
      return existingKey === mealKey || m.meal_type === meal.meal_type;
    });
    
    if (existingMealIndex >= 0) {
      // Si existe, combinar los items (evitando duplicados de items)
      const existingMeal = acc[existingMealIndex];
      const newItems = meal.items.filter(newItem => 
        !existingMeal.items.some(existingItem => 
          existingItem.food_name === newItem.food_name && 
          existingItem.serving_qty === newItem.serving_qty &&
          existingItem.serving_unit === newItem.serving_unit
        )
      );
      existingMeal.items = [...existingMeal.items, ...newItems];
    } else {
      // Si no existe, agregar la comida normalizada
      acc.push({
        ...meal,
        name: normalizedName
      });
    }
    
    return acc;
  }, []);
  
  if (normalizedMeals.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="mb-6">
          <Utensils className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            No hay comidas registradas
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Crea la estructura básica de comidas o ve al plan semanal para planificar tu día.
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={() => createDefaults.mutate()}
            disabled={createDefaults.isPending}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            {createDefaults.isPending ? 'Creando...' : 'Crear estructura básica'}
          </Button>
          <Button variant="secondary" asChild>
            <Link to="/nutrition/plan" className="gap-2">
              <Calendar className="h-4 w-4" />
              Ir al plan semanal
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const consumed = Number(data.totals?.calories_kcal) || 0;
  const target = data.targets?.calories_target ?? 2000;
  const progress = Math.min(100, Math.round((consumed / target) * 100));

  return (
    <div className="space-y-6 p-6">
      {/* Progress Card */}
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Progreso del día
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Adherencia: {progress}%
                </p>
              </div>
            </div>
            {data.meals.length > normalizedMeals.length && (
              <Button
                variant="secondary"
                onClick={() => cleanupDuplicates.mutate()}
                disabled={cleanupDuplicates.isPending}
                className="gap-2 text-orange-600 border-orange-200 hover:bg-orange-50"
              >
                <AlertCircle className="h-4 w-4" />
                {cleanupDuplicates.isPending ? 'Limpiando...' : 'Limpiar duplicados'}
              </Button>
            )}
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
              <div 
                className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
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

        {/* Meals */}
        <div className="space-y-6">
          {normalizedMeals.map((meal: Meal) => {
            const mealColor = mealColors[meal.meal_type] || 'gray';
            const mealIcon = mealIcons[meal.meal_type] || <Utensils className="h-5 w-5" />;
            const mealCalories = meal.items.reduce((sum, item) => {
              const calories = Number(item.calories_kcal) || 0;
              return sum + calories;
            }, 0);
            
            return (
              <Card key={meal.id} className="overflow-hidden">
                {/* Meal Header */}
                <div className={`bg-gradient-to-r from-${mealColor}-50 to-${mealColor}-100 dark:from-${mealColor}-900/20 dark:to-${mealColor}-800/20 p-4 border-b border-${mealColor}-200 dark:border-${mealColor}-700`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 bg-${mealColor}-100 dark:bg-${mealColor}-900/30 rounded-lg`}>
                        {mealIcon}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {meal.name || meal.meal_type}
                        </h3>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <CaloriesDisplay calories={Math.round(mealCalories)} />
                          <span>kcal</span>
                          <span>•</span>
                          <span>{meal.items.length} alimentos</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {/* Solo permitir editar nombres de comidas que no sean las principales */}
                      {!mainMealTypes.includes(meal.meal_type) && (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            const name = prompt('Nuevo nombre', meal.name || '');
                            if (name) updateMeal(meal.id, { name }).then(() =>
                              qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                            );
                          }}
                          className="gap-1 text-sm px-2 py-1"
                        >
                          <Edit3 className="h-3 w-3" />
                          Editar
                        </Button>
                      )}
                      {/* Solo permitir borrar comidas que no sean las principales */}
                      {!mainMealTypes.includes(meal.meal_type) && (
                        <Button
                          variant="secondary"
                          onClick={() => deleteMeal(meal.id).then(() =>
                            qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                          )}
                          className="gap-1 text-sm px-2 py-1 text-red-600 border-red-200 hover:bg-red-50"
                        >
                          <Trash2 className="h-3 w-3" />
                          Borrar
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Meal Items */}
                <div className="p-4">
                  {meal.items.length > 0 ? (
                    <div className="space-y-3 mb-4">
                      {meal.items.map((item) => (
                        <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 dark:text-white">
                              {item.food_name}
                            </div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                              {item.serving_qty} {item.serving_unit}
                            </div>
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
                                onClick={() =>
                                  deleteMealItem(meal.id, item.id).then(() =>
                                    qc.invalidateQueries({ queryKey: ['nutrition-day', date] })
                                  )
                                }
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

                  {/* Food Picker */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
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
                      useSmartSearch={true}
                      searchContext={mealTypeNames[meal.meal_type]}
                    />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
    </div>
  );
}