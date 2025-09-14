import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getMealPlan, getMealActuals, setMealActuals } from '../utils/storage';
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
    const plan = getMealPlan();
    const actuals = getMealActuals();
    
    // Usar la fecha objetivo o la fecha actual
    const dateToSync = targetDate || currentDate;
    
    // Obtener el día en formato del plan (Mon, Tue, etc.)
    const dayKey = getDayKeyFromDate(dateToSync);
    
    // Si hay plan para el día, sincronizarlo automáticamente
    if (plan[dayKey]) {
      const dayPlan = plan[dayKey];
      
      // Sincronizar cada comida del plan
      for (const [mealType, items] of Object.entries(dayPlan)) {
        if (items.length > 0) {
          await syncDayToBackend(dateToSync, mealType, items);
        }
      }
      
      // Actualizar los actuals para reflejar que se sincronizó
      const nextActuals = { ...actuals };
      nextActuals[dayKey] = { ...dayPlan };
      setMealActuals(nextActuals);
      
      // Invalidar la query de comidas del día para refrescar la UI
      queryClient.invalidateQueries({ queryKey: ['nutrition-day', dateToSync] });
    }
  };

  // Función para sincronizar cuando se agrega un alimento individual
  const syncIndividualFood = async (mealType: string, foodName: string, targetDate?: string) => {
    const dateToSync = targetDate || currentDate;
    const dayKey = getDayKeyFromDate(dateToSync);
    const actuals = getMealActuals();
    
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
    const nextActuals = { ...actuals };
    if (!nextActuals[dayKey]) {
      nextActuals[dayKey] = {};
    }
    if (!nextActuals[dayKey][planMealType]) {
      nextActuals[dayKey][planMealType] = [];
    }
    
    // Evitar duplicados
    if (!nextActuals[dayKey][planMealType].includes(foodName)) {
      nextActuals[dayKey][planMealType].push(foodName);
      setMealActuals(nextActuals);
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
      
      // Actualizar localStorage
      const actuals = getMealActuals();
      const currentDayKey = getCurrentDayKey();
      const nextActuals = { ...actuals };
      nextActuals[currentDayKey] = backendMeals;
      setMealActuals(nextActuals);
      
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
