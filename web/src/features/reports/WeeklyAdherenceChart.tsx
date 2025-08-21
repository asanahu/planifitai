import { useQuery } from '@tanstack/react-query';
import { getUserRoutines } from '../../api/routines';
import { listProgress } from '../../api/progress';
import { getSummary } from '../../api/nutrition';
import { today, daysAgo } from '../../utils/date';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Skeleton } from '../../components/ui/Skeleton';

export default function WeeklyAdherenceChart() {
  const end = today();
  const start = daysAgo(6);
  const routinesQ = useQuery({ queryKey: ['routines'], queryFn: getUserRoutines });
  const workoutsQ = useQuery({
    queryKey: ['workout-progress', start, end],
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    queryFn: () => listProgress({ metric: 'workout', start, end }) as any,
  });
  const nutritionQ = useQuery({
    queryKey: ['nutrition-summary', start, end],
    queryFn: () => getSummary(start, end),
  });

  if (routinesQ.isLoading || workoutsQ.isLoading || nutritionQ.isLoading) {
    return <Skeleton className="h-40" />;
  }

  const planned = routinesQ.data
    ? routinesQ.data.reduce(
        (acc, r) => acc + r.days.filter((d) => d.date >= start && d.date <= end).length,
        0
      )
    : 0;
  const done = workoutsQ.data ? workoutsQ.data.length : 0;
  const nutritionDays = nutritionQ.data ? nutritionQ.data.length : 0;
  const nutritionOk = nutritionQ.data
    ? nutritionQ.data.filter((d) => d.target && d.calories <= d.target).length
    : 0;

  const data = [
    { name: 'Entrenos', cumplido: done, faltante: Math.max(planned - done, 0) },
    {
      name: 'Nutrición',
      cumplido: nutritionOk,
      faltante: Math.max(nutritionDays - nutritionOk, 0),
    },
  ];

  return (
    <div role="img" aria-label="Adherencia semanal">
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="cumplido" stackId="a" fill="#82ca9d" />
          <Bar dataKey="faltante" stackId="a" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
