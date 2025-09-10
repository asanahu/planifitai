import { useState, useEffect, Suspense, lazy } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { addEntry, getEntries, type ProgressEntry } from '../api/progress';
import { today, daysAgo } from '../utils/date';
const WeightChart = lazy(() => import('../features/progress/WeightChart'));
const CaloriesChart = lazy(() => import('../features/progress/CaloriesChart'));
const WeeklyAdherenceChart = lazy(() => import('../features/reports/WeeklyAdherenceChart'));
import { loadAchievements } from '../utils/achievements';
import AchievementBadge from '../components/AchievementBadge';
import { Skeleton } from '../components/ui/Skeleton';
import Overlay from '../components/ui/Overlay';
import PageHeader from '../components/layout/PageHeader';

export default function ProgressPage() {
  const qc = useQueryClient();
  const [value, setValue] = useState('');
  const [tab, setTab] = useState<'weight' | 'calories' | 'adherence' | 'achievements'>('weight');
  const [achievements, setAchievements] = useState(loadAchievements());
  const date = today();
  const startWeek = daysAgo(6);
  const entriesQuery = useQuery({
    queryKey: ['progress', 'weight', startWeek, date],
    queryFn: () => getEntries('weight', startWeek, date),
  });
  const mutation = useMutation({
    mutationFn: () => addEntry({ metric: 'weight', value: Number(value), date }),
    onSuccess: () => {
      setValue('');
      qc.invalidateQueries({ queryKey: ['progress'] });
    },
  });

  useEffect(() => {
    setAchievements(loadAchievements());
  }, [tab]);

  return (
    <>
    <div className="space-y-4 p-3 md:p-6">
      <PageHeader>
        <h1 className="text-xl font-semibold">Progreso</h1>
        <p className="text-sm opacity-90">Peso, calorías y adherencia</p>
      </PageHeader>
      <div className="flex gap-2">
        {['weight', 'calories', 'adherence', 'achievements'].map((t) => (
          <button
            key={t}
            className={`px-2 py-1 text-sm ${tab === t ? 'font-semibold' : ''}`}
            onClick={() =>
              setTab(
                t as 'weight' | 'calories' | 'adherence' | 'achievements'
              )
            }
          >
            {t === 'weight'
              ? 'Peso'
              : t === 'calories'
              ? 'Calorías'
              : t === 'adherence'
              ? 'Adherencia'
              : 'Logros'}
          </button>
        ))}
      </div>

      {tab === 'weight' && (
        <>
          <div className="flex items-center gap-2">
            <label htmlFor="progress-weight" className="text-sm">
              Peso
            </label>
            <input
              id="progress-weight"
              className="w-24 rounded border p-2 text-sm"
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
            <button
              className="h-10 rounded bg-blue-500 px-4 text-white disabled:opacity-50"
              disabled={!value || mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? 'Guardando…' : 'Guardar peso'}
            </button>
          </div>
          {entriesQuery.isLoading ? (
            <Skeleton className="h-20" />
          ) : (
            <ul className="text-sm">
              {entriesQuery.data?.map((e: ProgressEntry) => (
                <li key={e.id}>
                  {e.date}: {e.value}kg
                </li>
              ))}
            </ul>
          )}
          <Suspense fallback={<Skeleton className="h-40" />}>
            <WeightChart />
          </Suspense>
        </>
      )}

      {tab === 'calories' && (
        <Suspense fallback={<Skeleton className="h-40" />}>
          <CaloriesChart />
        </Suspense>
      )}
      {tab === 'adherence' && (
        <Suspense fallback={<Skeleton className="h-40" />}>
          <WeeklyAdherenceChart />
        </Suspense>
      )}
      {tab === 'achievements' && (
        <div className="flex flex-wrap gap-2">
          {achievements.length === 0 && <p className="text-sm">Sin logros aún</p>}
          {achievements.map((a) => (
            <AchievementBadge
              key={a.id}
              title={a.title}
              icon={a.icon}
              dateUnlocked={a.dateUnlocked}
            />
          ))}
        </div>
      )}
    </div>
    {mutation.isPending && <Overlay>Guardando tu registro…</Overlay>}
    </>
  );
}
