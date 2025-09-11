import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { TodayWorkoutCard } from '../features/today/TodayWorkoutCard';
import { TodayNutritionCard } from '../features/today/TodayNutritionCard';
import { QuickWeighCard } from '../features/today/QuickWeighCard';
import { TodayReminders } from '../features/today/TodayReminders';
import KpiCard from '../components/KpiCard';
import { getPlannedDayFor } from '../api/routines';
import { getDayLog, getSummary } from '../api/nutrition';
import { listProgress } from '../api/progress';
import { today, daysAgo } from '../utils/date';
import { calcWeekAdherence, type WeekMeal, type WeekWorkout } from '../utils/adherence';
import { loadAchievements } from '../utils/achievements';
import AchievementBadge from '../components/AchievementBadge';
import { Dumbbell, CheckCircle, Flame, Scale } from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/card';
import Button from '../components/ui/button';
import { Sparkles } from 'lucide-react';

export default function TodayPage() {
  const date = today();
  const routineQuery = useQuery({
    queryKey: ['routine-day', date],
    queryFn: () => getPlannedDayFor(new Date(date)),
  });
  const progressQuery = useQuery({
    queryKey: ['workout-progress', date],
    queryFn: () => listProgress({ metric: 'workout', start: daysAgo(7), end: date }),
  });
  const nutritionQuery = useQuery({
    queryKey: ['nutrition', date],
    queryFn: () => getDayLog(date),
  });
  const nutritionWeekQuery = useQuery({
    queryKey: ['nutrition-summary', daysAgo(6), date],
    queryFn: () => getSummary(daysAgo(6), date),
  });
  const weightQuery = useQuery({
    queryKey: ['weight-30d', date],
    queryFn: () => listProgress({ metric: 'weight', start: daysAgo(30), end: date }),
  });

  if (!routineQuery.data && (!nutritionQuery.data || nutritionQuery.data.meals.length === 0)) {
    return (
      <div className="p-4 md:p-8">
        <div className="mx-auto max-w-3xl">
          <PageHeader className="mb-4 animate-fade-in">
            <h1 className="text-2xl font-semibold">Resumen de hoy</h1>
            <p className="text-sm opacity-90">No tienes actividades hoy. ¡Empieza creando tu plan!</p>
          </PageHeader>
          <Card className="text-center animate-fade-in" style={{ animationDelay: '80ms' }}>
            <div className="mx-auto mb-3 grid h-16 w-16 place-items-center rounded-full bg-planifit-50 text-planifit-600">
              <Dumbbell className="h-8 w-8" />
            </div>
            <p className="mb-1 text-lg font-medium">No tienes actividades hoy</p>
            <p className="mx-auto mb-4 max-w-md text-sm opacity-80">Crea tu rutina o añade tu primera comida.</p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <Link to="/workout/generate" role="button" aria-label="Crear rutina" tabIndex={0}>
                <Button className="inline-flex items-center gap-2">
                  <Sparkles className="h-4 w-4" /> Crear rutina
                </Button>
              </Link>
              <Link
                to="/nutrition/today"
                role="button"
                aria-label="Añadir comida"
                tabIndex={0}
                className="inline-flex items-center gap-2 rounded-md border px-4 py-2 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500"
              >
                <Flame className="h-4 w-4" /> Añadir comida
              </Link>
              <Link
                to="/progress"
                role="button"
                aria-label="Registrar peso"
                tabIndex={0}
                className="inline-flex items-center gap-2 rounded-md border px-4 py-2 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500"
              >
                <Scale className="h-4 w-4" /> Registrar peso
              </Link>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  let sessionsVal: string | number = '-';
  let adherenceVal: string | number = '-';
  let adhOverall = 0;
  if (routineQuery.data) {
    const { routine } = routineQuery.data;
    const activeDays = new Array(7).fill(false);
    routine.days.forEach((d) => {
      const idx = (new Date(d.date).getDay() + 6) % 7;
      activeDays[idx] = true;
    });
    const doneSet = new Set((progressQuery.data ?? []).map((p) => ((new Date(p.date).getDay() + 6) % 7)));
    const workouts: WeekWorkout[] = activeDays.map((active, idx) => ({
      planned: active,
      completed: active && doneSet.has(idx),
    }));
    const planned = workouts.filter((w) => w.planned).length;
    const done = workouts.filter((w) => w.completed).length;
    sessionsVal = `${done}/${planned}`;
    const workoutsPct = planned === 0 ? 0 : Math.round((done / planned) * 100);
    // Nutrition adherence: soporta dos formatos: lista de días o resumen con adherence
    let nutritionPct = 0;
    const nw: any = nutritionWeekQuery.data;
    if (Array.isArray(nw)) {
      const meals: WeekMeal[] = nw.map((d: any) => ({ target: d.target || 0, calories: d.calories || 0 }));
      const adh = calcWeekAdherence(workouts, meals);
      nutritionPct = adh.nutritionPct;
      adhOverall = adh.overallPct;
      adherenceVal = `${adh.overallPct}%`;
    } else if (nw && typeof nw === 'object' && nw.adherence) {
      nutritionPct = Math.round(((nw.adherence?.calories ?? 0) * 100));
      adhOverall = Math.round((workoutsPct + nutritionPct) / 2);
      adherenceVal = `${adhOverall}%`;
    } else {
      adhOverall = workoutsPct;
      adherenceVal = `${workoutsPct}%`;
    }
  }

  const kcalVal = nutritionQuery.data?.targets?.calories_target ?? '-';
  const entries = weightQuery.data ?? [];
  const delta =
    entries.length > 1 ? entries[entries.length - 1].value - entries[0].value : 0;
  const deltaStr = `${delta >= 0 ? '+' : ''}${delta.toFixed(1)} kg`;

  const achievements = loadAchievements().slice(-2);
  const microcopy =
    adhOverall >= 80
      ? `Vas genial, llevas ${adhOverall}% de adherencia`
      : 'Esta semana puedes mejorar tu constancia';

  return (
    <div className="space-y-3 p-3 md:p-6">
      <PageHeader className="animate-fade-in">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Resumen de hoy</h1>
            <p className="text-sm opacity-90">Tu actividad y nutrición de un vistazo</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1 text-sm animate-slide-up" style={{ animationDelay: '60ms' }}>
              <Dumbbell className="h-4 w-4" /> Sesiones {sessionsVal}
            </div>
            <div className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1 text-sm animate-slide-up" style={{ animationDelay: '120ms' }}>
              <CheckCircle className="h-4 w-4" /> Adherencia {adherenceVal}
            </div>
            <div className="flex items-center gap-2 rounded-md bg-white/10 px-3 py-1 text-sm animate-slide-up" style={{ animationDelay: '180ms' }}>
              <Flame className="h-4 w-4" /> Meta {kcalVal} kcal
            </div>
          </div>
        </div>
      </PageHeader>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="animate-slide-up" style={{ animationDelay: '80ms' }}>
          <KpiCard title="Sesiones semana" value={sessionsVal} icon={<Dumbbell className="h-4 w-4" />} />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '120ms' }}>
          <KpiCard title="Adherencia" value={adherenceVal} icon={<CheckCircle className="h-4 w-4" />} />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '160ms' }}>
          <KpiCard title="Meta kcal hoy" value={kcalVal} icon={<Flame className="h-4 w-4" />} />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
          <KpiCard title="Delta peso 30d" value={deltaStr} icon={<Scale className="h-4 w-4" />} />
        </div>
      </div>
      {adherenceVal !== '-' && (
        <Card className="animate-fade-in" style={{ animationDelay: '220ms' }}>
          <div className="text-sm">🔥 {adherenceVal} semana</div>
        </Card>
      )}
      <p className="text-sm animate-fade-in" style={{ animationDelay: '260ms' }}>{microcopy}</p>
      {achievements.length > 0 && (
        <div className="space-y-1 animate-fade-in" style={{ animationDelay: '300ms' }}>
          <h3 className="text-sm font-semibold">Logros recientes</h3>
          <div className="flex gap-2">
            {achievements.map((a) => (
              <AchievementBadge key={a.id} title={a.title} icon={a.icon} dateUnlocked={a.dateUnlocked} />
            ))}
          </div>
        </div>
      )}
      <div className="animate-fade-in" style={{ animationDelay: '340ms' }}>
        <TodayReminders />
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <div className="animate-slide-up" style={{ animationDelay: '120ms' }}>
          <TodayWorkoutCard />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '160ms' }}>
          <TodayNutritionCard />
        </div>
        <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
          <QuickWeighCard />
        </div>
      </div>
    </div>
  );
}
