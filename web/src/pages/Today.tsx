import { useQuery } from '@tanstack/react-query';
import { TodayWorkoutCard } from '../features/today/TodayWorkoutCard';
import { TodayNutritionCard } from '../features/today/TodayNutritionCard';
import { QuickWeighCard } from '../features/today/QuickWeighCard';
import { TodayReminders } from '../features/today/TodayReminders';
import KpiCard from '../components/KpiCard';
import { getPlannedDayFor } from '../api/routines';
import { getDayLog } from '../api/nutrition';
import { listProgress } from '../api/progress';
import { today, daysAgo } from '../utils/date';
import { calcWeekAdherence } from '../utils/adherence';
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
  const weightQuery = useQuery({
    queryKey: ['weight-30d', date],
    queryFn: () => listProgress({ metric: 'weight', start: daysAgo(30), end: date }),
  });

  let sessionsVal: string | number = '-';
  let adherenceVal: string | number = '-';
  if (routineQuery.data) {
    const { routine } = routineQuery.data;
    const activeDays = new Array(7).fill(false);
    routine.days.forEach((d) => {
      const idx = (new Date(d.date).getDay() + 6) % 7;
      activeDays[idx] = true;
    });
    const adh = calcWeekAdherence({
      activeDays,
      workoutsDone: (progressQuery.data ?? []).map((p) => new Date(p.date)),
    });
    sessionsVal = `${adh.countDone}/${adh.countPlanned}`;
    adherenceVal = `${adh.rate}%`;
  }

  const kcalVal = nutritionQuery.data?.targets?.calories ?? '-';
  const entries = weightQuery.data ?? [];
  const delta =
    entries.length > 1 ? entries[entries.length - 1].value - entries[0].value : 0;
  const deltaStr = `${delta >= 0 ? '+' : ''}${delta.toFixed(1)} kg`;

  return (
    <div className="space-y-3 p-3 md:p-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCard title="Sesiones semana" value={sessionsVal} icon={<Dumbbell className="h-4 w-4" />} />
        <KpiCard title="Adherencia" value={adherenceVal} icon={<CheckCircle className="h-4 w-4" />} />
        <KpiCard title="Meta kcal hoy" value={kcalVal} icon={<Flame className="h-4 w-4" />} />
        <KpiCard title="Delta peso 30d" value={deltaStr} icon={<Scale className="h-4 w-4" />} />
      </div>
      <TodayReminders />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <TodayWorkoutCard />
        <TodayNutritionCard />
        <QuickWeighCard />
      </div>
    </div>
  );
}
