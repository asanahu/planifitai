import { searchFoods } from '../api/nutrition';

// Caché global para evitar búsquedas repetidas
const globalCaloriesCache = new Map<string, number>();

// Función para estimar calorías basada en el nombre del alimento
export function estimateCaloriesFromFoodName(foodName: string): number {
  const name = foodName.toLowerCase();
  
  // Estimaciones básicas por tipo de alimento (por 100g o porción típica)
  
  // Carnes y pescados
  if (name.includes('pollo') || name.includes('pavo')) return 165;
  if (name.includes('pechuga')) return 165;
  if (name.includes('atún') || name.includes('salmon') || name.includes('salmón')) return 184;
  if (name.includes('pescado')) return 206;
  if (name.includes('ternera') || name.includes('res')) return 250;
  if (name.includes('cerdo')) return 242;
  if (name.includes('huevo')) return 155;
  
  // Cereales y granos
  if (name.includes('arroz')) return 130;
  if (name.includes('pasta')) return 130;
  if (name.includes('avena')) return 389;
  if (name.includes('quinoa')) return 368;
  if (name.includes('cuscus')) return 112;
  if (name.includes('maiz')) return 365;
  if (name.includes('pan')) return 250;
  
  // Lácteos
  if (name.includes('leche')) return 60;
  if (name.includes('yogur')) return 60;
  if (name.includes('queso')) return 350;
  if (name.includes('nata')) return 345;
  if (name.includes('kefir')) return 41;
  
  // Frutas
  if (name.includes('manzana')) return 52;
  if (name.includes('pera')) return 52;
  if (name.includes('plátano') || name.includes('banana')) return 89;
  if (name.includes('fresa')) return 32;
  if (name.includes('uva')) return 67;
  if (name.includes('kiwi')) return 61;
  if (name.includes('mango')) return 60;
  if (name.includes('pina')) return 50;
  if (name.includes('limon')) return 29;
  if (name.includes('arandano')) return 57;
  
  // Verduras
  if (name.includes('tomate')) return 18;
  if (name.includes('lechuga')) return 15;
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
  
  // Tubérculos
  if (name.includes('patata') || name.includes('papa')) return 77;
  if (name.includes('boniato') || name.includes('batata')) return 86;
  
  // Legumbres
  if (name.includes('lentejas')) return 116;
  if (name.includes('garbanzos')) return 116;
  if (name.includes('alubia') || name.includes('judia')) return 127;
  if (name.includes('tofu')) return 76;
  if (name.includes('soja')) return 446;
  
  // Frutos secos y semillas
  if (name.includes('nuez')) return 575;
  if (name.includes('almendra')) return 575;
  if (name.includes('cacahuete')) return 567;
  if (name.includes('avellana')) return 628;
  if (name.includes('pistacho')) return 562;
  if (name.includes('anacardo')) return 553;
  if (name.includes('semilla')) return 534;
  
  // Grasas y aceites
  if (name.includes('aceite')) return 884;
  if (name.includes('mantequilla')) return 717;
  if (name.includes('aguacate')) return 160;
  
  // Condimentos y especias
  if (name.includes('sal')) return 0;
  if (name.includes('azucar')) return 387;
  if (name.includes('vinagre')) return 19;
  if (name.includes('pimienta')) return 251;
  if (name.includes('especias')) return 252;
  if (name.includes('salsa')) return 30;
  
  // Bebidas
  if (name.includes('agua')) return 0;
  if (name.includes('zumo') || name.includes('jugo')) return 45;
  if (name.includes('cafe')) return 2;
  if (name.includes('te')) return 1;
  
  // Por defecto, estimar 100 kcal para alimentos no reconocidos
  return 100;
}

// Función para determinar si un alimento necesita búsqueda en API
export function needsApiSearch(foodName: string): boolean {
  const estimated = estimateCaloriesFromFoodName(foodName);
  return estimated === 100; // Solo buscar si tiene valor por defecto
}

// Función principal para calcular calorías de un alimento
export async function calculateFoodCalories(foodName: string): Promise<{
  calories: number;
  source: 'cache' | 'estimation' | 'api';
}> {
  // Limpiar el nombre del alimento (remover cantidades)
  const cleanName = foodName.replace(/^\d+[\.,]?\d*\s*[a-zA-Z]*\s*/, '').trim();
  
  // Verificar caché primero
  if (globalCaloriesCache.has(cleanName)) {
    return {
      calories: globalCaloriesCache.get(cleanName)!,
      source: 'cache'
    };
  }

  // Usar estimación local primero (más rápido)
  let calories = estimateCaloriesFromFoodName(cleanName);
  let source: 'estimation' | 'api' = 'estimation';
  
  // Solo buscar en API si es necesario y no está en caché
  if (needsApiSearch(cleanName)) {
    try {
      const foods = await searchFoods(cleanName, 1, 3);
      if (foods.length > 0 && foods[0].calories_kcal) {
        calories = foods[0].calories_kcal;
        source = 'api';
      }
    } catch (error) {
      console.warn(`Error buscando alimento "${cleanName}":`, error);
      // Mantener la estimación local
    }
  }
  
  // Guardar en caché
  globalCaloriesCache.set(cleanName, calories);
  
  return { calories, source };
}

// Función para limpiar el caché global
export function clearGlobalCaloriesCache(): void {
  globalCaloriesCache.clear();
  console.log('🧹 Caché global de calorías limpiado');
}

// Función para obtener estadísticas del caché
export function getCacheStats(): { size: number; keys: string[] } {
  return {
    size: globalCaloriesCache.size,
    keys: Array.from(globalCaloriesCache.keys())
  };
}
