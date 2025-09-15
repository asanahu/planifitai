import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getMealPlanForWeek, getMealActualsForWeek, setMealActualsForWeek } from '../utils/storage';
import { today } from '../utils/date';
import { createMeal, addMealItemFlexible, getDayLog } from '../api/nutrition';
import { calculateFoodCalories } from '../utils/caloriesCalculator';

/**
 * Hook para sincronizar automáticamente el plan semanal con las comidas reales
 * y las comidas de hoy en el backend
 */
export function useAutoSyncMeals() {
  const queryClient = useQueryClient();
  const currentDate = today();

  // Utilidades locales para semanas (actual y siguiente)
  const formatYMDLocal = (d: Date) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  const getWeekDatesLocal = (weekKey: 'week1' | 'week2'): string[] => {
    const now = new Date();
    const dow = now.getDay();
    const mondayOffset = dow === 0 ? -6 : 1 - dow;
    const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    monday.setDate(monday.getDate() + mondayOffset + (weekKey === 'week2' ? 7 : 0));
    const dates: string[] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate());
      d.setDate(monday.getDate() + i);
      dates.push(formatYMDLocal(d));
    }
    return dates;
  };

  const getWeekKeyForDate = (date: string): 'week1' | 'week2' => {
    const w1 = getWeekDatesLocal('week1');
    if (w1.includes(date)) return 'week1';
    const w2 = getWeekDatesLocal('week2');
    if (w2.includes(date)) return 'week2';
    return 'week1';
  };

  // Función para sincronizar un día específico
  const syncDayToBackend = async (day: string, mealType: string, items: string[]) => {
    try {
      // Mapear tipos del plan a tipos del backend
      const mealTypeMap: Record<string, 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'other'> = {
        'Breakfast': 'breakfast',
        'Lunch': 'lunch',
        'Dinner': 'dinner', 
        'Snack': 'snack',
        'Other': 'other'
      };
      
      const backendMealType = mealTypeMap[mealType] || 'other';
      
      // Obtener las comidas existentes para el día
      const existingMeals = await queryClient.fetchQuery({
        queryKey: ['nutrition-day', day],
        queryFn: () => getDayLog(day)
      });
      
      // Buscar si ya existe una comida del mismo tipo
      let existingMeal = existingMeals?.meals.find(m => m.meal_type === backendMealType);
      
      if (!existingMeal) {
        // Crear la comida si no existe
        existingMeal = await createMeal({ 
          date: day, 
          meal_type: backendMealType, 
          name: getMealName(mealType)
        });
      }

      // Agregar cada item de la comida
      for (const item of items) {
        if (item.trim()) {
          try {
            // Calcular calorías reales para el alimento usando función compartida
            const result = await calculateFoodCalories(item.trim());
            
            console.log(`🍎 Agregando ${item.trim()}: ${result.calories} kcal (${result.source})`);
            
            await addMealItemFlexible(existingMeal.id, {
              food_name: item.trim(),
              serving_qty: 1,
              serving_unit: 'unit',
              calories_kcal: result.calories,
              protein_g: Math.round(result.calories * 0.15), // Estimación: 15% proteína
              carbs_g: Math.round(result.calories * 0.55),   // Estimación: 55% carbohidratos
              fat_g: Math.round(result.calories * 0.30)      // Estimación: 30% grasa
            });
          } catch (itemError) {
            console.error(`Error agregando item ${item}:`, itemError);
          }
        }
      }
    } catch (error) {
      console.error(`Error sincronizando ${mealType} del ${day}:`, error);
    }
  };

  // Función para sincronizar todo el día actual
  const syncCurrentDay = async (targetDate?: string) => {
    const dateToSync = targetDate || currentDate;
    const weekKey = getWeekKeyForDate(dateToSync);
    const plan = getMealPlanForWeek(weekKey);
    const actuals = getMealActualsForWeek(weekKey);
    
    // Obtener el día en formato del plan (Mon, Tue, etc.)
    const dayKey = getDayKeyFromDate(dateToSync);
    
    // Si hay plan para el día, sincronizarlo automáticamente
    if (plan[dayKey]) {
      const dayPlan = plan[dayKey];
      
      // Sincronizar cada comida del plan
      for (const [mealType, items] of Object.entries(dayPlan)) {
        if (items.length > 0) {
          await syncDayToBackend(dateToSync, mealType, items as string[]);
        }
      }
      
      // Actualizar los actuals para reflejar que se sincronizó
      const nextActuals = { ...actuals } as any;
      nextActuals[dayKey] = { ...dayPlan };
      setMealActualsForWeek(weekKey, nextActuals);
      
      // Invalidar la query de comidas del día para refrescar la UI
      queryClient.invalidateQueries({ queryKey: ['nutrition-day', dateToSync] });
    }
  };

  // Función para sincronizar cuando se agrega un alimento individual
  const syncIndividualFood = async (mealType: string, foodName: string, targetDate?: string) => {
    const dateToSync = targetDate || currentDate;
    const weekKey = getWeekKeyForDate(dateToSync);
    const dayKey = getDayKeyFromDate(dateToSync);
    const actuals = getMealActualsForWeek(weekKey);

    // Mapear tipos del backend a tipos del plan
    const planMealTypeMap: Record<string, string> = {
      'breakfast': 'Breakfast',
      'lunch': 'Lunch',
      'dinner': 'Dinner',
      'snack': 'Snack',
      'other': 'Other'
    };
    
    const planMealType = planMealTypeMap[mealType] || 'Other';
    
    // Agregar el alimento a los actuals
    const nextActuals = { ...actuals } as any;
    if (!nextActuals[dayKey]) {
      nextActuals[dayKey] = {};
    }
    if (!nextActuals[dayKey][planMealType]) {
      nextActuals[dayKey][planMealType] = [];
    }
    
    // Evitar duplicados
    if (!nextActuals[dayKey][planMealType].includes(foodName)) {
      nextActuals[dayKey][planMealType].push(foodName);
      setMealActualsForWeek(weekKey, nextActuals);
    }
    
    // Sincronizar con el backend
    await syncDayToBackend(dateToSync, planMealType, [foodName]);
    
    // Invalidar la query para refrescar la UI
    queryClient.invalidateQueries({ queryKey: ['nutrition-day', dateToSync] });
  };

  // Función para sincronizar desde el backend hacia localStorage
  const syncBackendToLocal = async (day: string) => {
    try {
      // Obtener las comidas del día desde el backend
      const dayLog = await getDayLog(day);
      
      // Convertir las comidas del backend al formato del plan
      const backendMeals: Record<string, string[]> = {};
      
      for (const meal of dayLog.meals) {
        const planMealType = getPlanMealType(meal.meal_type);
        if (!backendMeals[planMealType]) {
          backendMeals[planMealType] = [];
        }
        
        // Agregar cada item de la comida
        for (const item of meal.items) {
          if (item.food_name) {
            backendMeals[planMealType].push(item.food_name);
          }
        }
      }
      
      // Actualizar localStorage semanal
      const weekKey = getWeekKeyForDate(day);
      const dayKey = getDayKeyFromDate(day);
      const actuals = getMealActualsForWeek(weekKey);
      const nextActuals = { ...actuals } as any;
      nextActuals[dayKey] = backendMeals;
      setMealActualsForWeek(weekKey, nextActuals);
      
      console.log('✅ Backend sincronizado con localStorage');
    } catch (error) {
      console.error('❌ Error sincronizando backend a localStorage:', error);
    }
  };

  return {
    syncCurrentDay,
    syncIndividualFood,
    syncBackendToLocal
  };
}

// Función auxiliar para obtener el día actual en formato del plan
function getCurrentDayKey(): string {
  const d = new Date().getDay(); // 0=Sun..6=Sat
  const map: Record<number, string> = { 0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat' };
  return map[d] ?? 'Mon';
}

// Función auxiliar para obtener el día de la semana desde una fecha ISO
function getDayKeyFromDate(dateString: string): string {
  const date = new Date(dateString);
  const day = date.getDay(); // 0=Sun..6=Sat
  const map: Record<number, string> = { 0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat' };
  return map[day] ?? 'Mon';
}

// Función auxiliar para obtener el nombre de la comida en español
function getMealName(mealType: string): string {
  const names: Record<string, string> = {
    'Breakfast': 'Desayuno',
    'Lunch': 'Comida', 
    'Dinner': 'Cena',
    'Snack': 'Merienda',
    'Other': 'Otro'
  };
  return names[mealType] || mealType;
}

// Función auxiliar para convertir tipo del backend a tipo del plan
function getPlanMealType(backendMealType: string): string {
  const map: Record<string, string> = {
    'breakfast': 'Breakfast',
    'lunch': 'Lunch',
    'dinner': 'Dinner',
    'snack': 'Snack',
    'other': 'Other'
  };
  return map[backendMealType] || 'Other';
}



