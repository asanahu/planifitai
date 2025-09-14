import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getDayLog, searchFoods } from '../../api/nutrition';
import { getMealPlan } from '../../utils/storage';
import { today } from '../../utils/date';
import Card from '../../components/ui/card';
import { Utensils, Target, TrendingUp } from 'lucide-react';

interface CaloriesData {
  planned: number;
  real: number;
  target: number;
  plannedPercentage: number;
  realPercentage: number;
}

// Caché para evitar búsquedas repetidas
const foodCaloriesCache = new Map<string, number>();

export default function CaloriesComparison() {
  const [selectedDate, setSelectedDate] = useState(today());
  const [caloriesData, setCaloriesData] = useState<CaloriesData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Obtener datos reales del día desde la API
  const { data: dayLog } = useQuery({
    queryKey: ['nutrition-day', selectedDate],
    queryFn: () => getDayLog(selectedDate),
  });

  // Calcular calorías planificadas con debounce
  const calculatePlannedCalories = useCallback(async () => {
    setIsLoading(true);
    try {
      const mealPlan = getMealPlan();
      // const mealActuals = getMealActuals(); // No usado por ahora
      
      // Obtener el día de la semana correspondiente a la fecha seleccionada
      const date = new Date(selectedDate);
      const dayOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()];
      
      const plannedItems = mealPlan[dayOfWeek] || {};
      
      // Calcular calorías planificadas buscando alimentos en la base de datos
      let plannedCalories = 0;
      
      // Recopilar todos los alimentos únicos del plan
      const uniqueFoods = new Set<string>();
      Object.values(plannedItems).forEach((items: string[]) => {
        items.forEach(item => {
          // Limpiar el nombre del alimento (remover cantidades)
          const cleanName = item.replace(/^\d+[\.,]?\d*\s*[a-zA-Z]*\s*/, '').trim();
          uniqueFoods.add(cleanName);
        });
      });
      
      // Calcular calorías para cada alimento
      for (const foodName of uniqueFoods) {
        // Verificar caché primero
        if (foodCaloriesCache.has(foodName)) {
          plannedCalories += foodCaloriesCache.get(foodName)!;
          continue;
        }

        // Usar estimación local primero (más rápido)
        let calories = estimateCaloriesFromFoodName(foodName);
        
        // Solo buscar en API si es necesario y no está en caché
        if (needsApiSearch(foodName)) {
          try {
            const foods = await searchFoods(foodName, 1, 3);
            if (foods.length > 0 && foods[0].calories_kcal) {
              calories = foods[0].calories_kcal;
            }
          } catch (error) {
            console.warn(`Error buscando alimento "${foodName}":`, error);
            // Mantener la estimación local
          }
        }
        
        // Guardar en caché
        foodCaloriesCache.set(foodName, calories);
        plannedCalories += calories;
      }
      
      const realCalories = dayLog?.totals?.calories_kcal || 0;
      const targetCalories = dayLog?.targets?.calories_target || 0;
      
      setCaloriesData({
        planned: Math.round(plannedCalories),
        real: realCalories,
        target: targetCalories,
        plannedPercentage: targetCalories > 0 ? (plannedCalories / targetCalories) * 100 : 0,
        realPercentage: targetCalories > 0 ? (realCalories / targetCalories) * 100 : 0,
      });
    } finally {
      setIsLoading(false);
    }
  }, [selectedDate, dayLog]);

  // Calcular calorías planificadas
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      calculatePlannedCalories();
    }, 300); // Debounce de 300ms

    return () => clearTimeout(timeoutId);
  }, [calculatePlannedCalories]);

  // Función para estimar calorías basada en el nombre del alimento
  const estimateCaloriesFromFoodName = (foodName: string): number => {
    const name = foodName.toLowerCase();
    
    // Estimaciones básicas por tipo de alimento (por 100g o porción típica)
    if (name.includes('pollo') || name.includes('pavo')) return 165;
    if (name.includes('arroz') || name.includes('pasta')) return 130;
    if (name.includes('pan')) return 250;
    if (name.includes('huevo')) return 155;
    if (name.includes('leche') || name.includes('yogur')) return 60;
    if (name.includes('queso')) return 350;
    if (name.includes('manzana') || name.includes('pera')) return 52;
    if (name.includes('plátano') || name.includes('banana')) return 89;
    if (name.includes('tomate')) return 18;
    if (name.includes('lechuga')) return 15;
    if (name.includes('aguacate')) return 160;
    if (name.includes('aceite')) return 884;
    if (name.includes('mantequilla')) return 717;
    if (name.includes('atún') || name.includes('salmon')) return 184;
    if (name.includes('lentejas') || name.includes('garbanzos')) return 116;
    if (name.includes('nuez') || name.includes('almendra')) return 575;
    if (name.includes('pechuga')) return 165;
    if (name.includes('ternera') || name.includes('res')) return 250;
    if (name.includes('cerdo')) return 242;
    if (name.includes('pescado')) return 206;
    if (name.includes('tofu')) return 76;
    if (name.includes('alubia') || name.includes('judia')) return 127;
    if (name.includes('avena')) return 389;
    if (name.includes('quinoa')) return 368;
    if (name.includes('cuscus')) return 112;
    if (name.includes('maiz')) return 365;
    if (name.includes('mantequilla')) return 717;
    if (name.includes('nata')) return 345;
    if (name.includes('kefir')) return 41;
    if (name.includes('cacahuete')) return 567;
    if (name.includes('avellana')) return 628;
    if (name.includes('pistacho')) return 562;
    if (name.includes('anacardo')) return 553;
    if (name.includes('semilla')) return 534;
    if (name.includes('sal')) return 0;
    if (name.includes('azucar')) return 387;
    if (name.includes('vinagre')) return 19;
    if (name.includes('pimienta')) return 251;
    if (name.includes('especias')) return 252;
    if (name.includes('salsa')) return 30;
    if (name.includes('soja')) return 446;
    if (name.includes('agua')) return 0;
    if (name.includes('zumo') || name.includes('jugo')) return 45;
    if (name.includes('cafe')) return 2;
    if (name.includes('te')) return 1;
    if (name.includes('zanahoria')) return 41;
    if (name.includes('pepino')) return 16;
    if (name.includes('pimiento')) return 31;
    if (name.includes('cebolla')) return 40;
    if (name.includes('ajo')) return 149;
    if (name.includes('espinaca')) return 23;
    if (name.includes('brocoli')) return 34;
    if (name.includes('coliflor')) return 25;
    if (name.includes('calabacin')) return 17;
    if (name.includes('berenjena')) return 25;
    if (name.includes('acelga')) return 19;
    if (name.includes('apio')) return 16;
    if (name.includes('fresa')) return 32;
    if (name.includes('uva')) return 67;
    if (name.includes('kiwi')) return 61;
    if (name.includes('mango')) return 60;
    if (name.includes('pina')) return 50;
    if (name.includes('limon')) return 29;
    if (name.includes('arandano')) return 57;
    
    // Por defecto, estimar 100 kcal para alimentos no reconocidos
    return 100;
  };

  // Función para determinar si un alimento necesita búsqueda en API
  const needsApiSearch = (foodName: string): boolean => {
    // Solo buscar en API alimentos que no están en nuestro diccionario
    return !estimateCaloriesFromFoodName(foodName) || estimateCaloriesFromFoodName(foodName) === 100;
  };

  const getDifference = () => {
    if (!caloriesData) return 0;
    return caloriesData.real - caloriesData.planned;
  };

  const getDifferenceColor = () => {
    const diff = getDifference();
    if (diff > 100) return 'text-red-600';
    if (diff < -100) return 'text-blue-600';
    return 'text-green-600';
  };

  if (isLoading || !caloriesData) {
    return (
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Utensils className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold">Comparación de Calorías</h3>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="text-sm text-gray-500 mt-2">
            {isLoading ? 'Calculando calorías planificadas...' : 'Cargando datos...'}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Utensils className="h-5 w-5 text-blue-500" />
        <h3 className="text-lg font-semibold">Comparación de Calorías</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Planificado */}
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-center gap-1 mb-2">
            <Target className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-800">Planificado</span>
          </div>
          <div className="text-2xl font-bold text-blue-600">{caloriesData.planned}</div>
          <div className="text-sm text-blue-600">kcal</div>
          <div className="text-xs text-gray-600">
            {caloriesData.plannedPercentage.toFixed(0)}% del objetivo
          </div>
        </div>

        {/* Real */}
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="flex items-center justify-center gap-1 mb-2">
            <Utensils className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Consumido</span>
          </div>
          <div className="text-2xl font-bold text-green-600">{caloriesData.real}</div>
          <div className="text-sm text-green-600">kcal</div>
          <div className="text-xs text-gray-600">
            {caloriesData.realPercentage.toFixed(0)}% del objetivo
          </div>
        </div>

        {/* Diferencia */}
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-1 mb-2">
            <TrendingUp className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-800">Diferencia</span>
          </div>
          <div className={`text-2xl font-bold ${getDifferenceColor()}`}>
            {getDifference() > 0 ? '+' : ''}{getDifference()}
          </div>
          <div className="text-sm text-gray-600">kcal</div>
          <div className="text-xs text-gray-600">
            {getDifference() > 0 ? 'Más de lo planificado' : 
             getDifference() < 0 ? 'Menos de lo planificado' : 'Exacto'}
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

      {/* Selector de fecha */}
      <div className="mt-4 pt-4 border-t">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Seleccionar fecha:
        </label>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </Card>
  );
}
