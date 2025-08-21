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
      <div className="p-3">
        <div className="space-y-2 rounded border bg-white p-4 shadow-sm dark:bg-gray-800">
          <p>No tienes actividades hoy. ¡Empieza creando tu plan!</p>
          <div className="flex flex-wrap gap-2 text-sm">
            <Link to="/workout/generate" className="rounded bg-blue-500 px-4 py-2 text-white">
              Crear rutina
            </Link>
            <Link to="/nutrition/today" className="rounded border px-4 py-2">
              Añadir comida
            </Link>
            <Link to="/progress" className="rounded border px-4 py-2">
              Registrar peso
            </Link>
          </div>
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
    const meals: WeekMeal[] = (nutritionWeekQuery.data || []).map((d) => ({
      target: d.target || 0,
      calories: d.calories || 0,
    }));
    const adh = calcWeekAdherence(workouts, meals);
    const planned = workouts.filter((w) => w.planned).length;
    const done = workouts.filter((w) => w.completed).length;
    sessionsVal = `${done}/${planned}`;
    adherenceVal = `${adh.overallPct}%`;
    adhOverall = adh.overallPct;
  }

  const kcalVal = nutritionQuery.data?.targets?.calories ?? '-';
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
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCard title="Sesiones semana" value={sessionsVal} icon={<Dumbbell className="h-4 w-4" />} />
        <KpiCard title="Adherencia" value={adherenceVal} icon={<CheckCircle className="h-4 w-4" />} />
        <KpiCard title="Meta kcal hoy" value={kcalVal} icon={<Flame className="h-4 w-4" />} />
        <KpiCard title="Delta peso 30d" value={deltaStr} icon={<Scale className="h-4 w-4" />} />
      </div>
      {adherenceVal !== '-' && (
        <div className="rounded bg-orange-100 p-2 text-sm">🔥 {adherenceVal} semana</div>
      )}
      <p className="text-sm">{microcopy}</p>
      {achievements.length > 0 && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold">Logros recientes</h3>
          <div className="flex gap-2">
            {achievements.map((a) => (
              <AchievementBadge key={a.id} title={a.title} icon={a.icon} dateUnlocked={a.dateUnlocked} />
            ))}
          </div>
        </div>
      )}
      <TodayReminders />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <TodayWorkoutCard />
        <TodayNutritionCard />
        <QuickWeighCard />
      </div>
    </div>
  );
}
