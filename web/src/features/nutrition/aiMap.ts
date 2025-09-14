import type { AiNutritionPlanJSON } from '../../api/ai';
import type { MealPlan } from '../../utils/storage';

export type LocalMealPlan = MealPlan;

const UI_DAYS: Array<'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun'> = [
  'Mon',
  'Tue',
  'Wed',
  'Thu',
  'Fri',
  'Sat',
  'Sun',
];
const DATE_DAY_ABBR = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function toUiDayKey(d: any, index: number): string {
  // Prefer ISO date -> map to weekday abbr expected by UI
  const dateStr: string | undefined = d?.date || d?.Day || d?.DAY;
  if (dateStr) {
    const dt = new Date(dateStr);
    if (!isNaN(dt.getTime())) {
      return DATE_DAY_ABBR[dt.getDay()];
    }
  }
  // Fallback: parse textual day
  const raw = String(d?.day || d?.weekday || '').toLowerCase();
  if (raw) {
    if (raw.startsWith('mon') || raw.startsWith('lun')) return 'Mon';
    if (raw.startsWith('tue') || raw.startsWith('mar')) return 'Tue';
    if (raw.startsWith('wed') || raw.startsWith('mié') || raw.startsWith('mie')) return 'Wed';
    if (raw.startsWith('thu') || raw.startsWith('jue')) return 'Thu';
    if (raw.startsWith('fri') || raw.startsWith('vie')) return 'Fri';
    if (raw.startsWith('sat') || raw.startsWith('sáb') || raw.startsWith('sab')) return 'Sat';
    if (raw.startsWith('sun') || raw.startsWith('dom')) return 'Sun';
  }
  // Last resort: sequential mapping Mon..Sun
  return UI_DAYS[index % 7];
}

function normalizeMealKey(m: any, j: number): string {
  const raw = String(m?.type || m?.name || '').toLowerCase();
  if (raw.startsWith('break')) return 'Breakfast';
  if (raw.startsWith('alm') || raw.startsWith('lunch') || raw === 'comida') return 'Lunch';
  if (raw.startsWith('din') || raw.startsWith('cena') || raw.startsWith('dinner')) return 'Dinner';
  if (raw.startsWith('snack') || raw.startsWith('meri')) return 'Snack';
  // default bucket
  return ['Breakfast', 'Lunch', 'Dinner', 'Snack'][j % 4];
}

function formatItem(it: any): string {
  if (typeof it === 'string') return it;
  const name = it?.name ?? 'item';
  const qty = it?.qty != null ? it.qty : it?.quantity;
  const unit = it?.unit ?? it?.serving_unit ?? '';
  if (qty) {
    return `${qty} ${unit} ${name}`.trim();
  }
  return String(name);
}

export function mapAiNutritionPlanToLocal(ai: AiNutritionPlanJSON): LocalMealPlan {
  const plan: LocalMealPlan = {};
  
  // Para 14 días, necesitamos crear claves únicas para cada día
  (ai.days ?? []).forEach((d, i) => {
    // Crear clave única para el día (día de la semana + número de semana)
    const baseDayKey = toUiDayKey(d as any, i);
    const weekNumber = Math.floor(i / 7) + 1;
    const dayKey = weekNumber === 1 ? baseDayKey : `${baseDayKey}_W${weekNumber}`;
    
    if (!plan[dayKey]) plan[dayKey] = {} as any;
    (d.meals ?? []).forEach((m, j) => {
      const mealKey = normalizeMealKey(m, j);
      const items = (m.items ?? []).map(formatItem);
      (plan as any)[dayKey][mealKey] = items;
    });
  });
  
  console.log('mapAiNutritionPlanToLocal - días procesados:', Object.keys(plan));
  return plan;
}

export function mapAiNutritionPlanToServer(ai: AiNutritionPlanJSON) {
  return ai as unknown;
}

