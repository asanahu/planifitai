import { useQuery } from '@tanstack/react-query';
import { getUserRoutines } from '../../api/routines';
import { listProgress, getEntries } from '../../api/progress';
import { today, daysAgo } from '../../utils/date';
import { Skeleton } from '../../components/ui/Skeleton';

export default function ReportSummary() {
  const end = today();
  const start = daysAgo(30);
  const routinesQ = useQuery({ queryKey: ['routines'], queryFn: getUserRoutines });
  const workoutsQ = useQuery({
    queryKey: ['workout-progress', start, end],
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    queryFn: () => listProgress({ metric: 'workout', start, end }) as any,
  });
  const weightQ = useQuery({
    queryKey: ['progress', 'weight', start, end],
    queryFn: () => getEntries('weight', start, end),
  });

  if (routinesQ.isLoading || workoutsQ.isLoading || weightQ.isLoading) {
    return <Skeleton className="h-20" />;
  }

  const planned = routinesQ.data
    ? routinesQ.data.reduce(
        (acc, r) => acc + r.days.filter((d) => d.date >= start && d.date <= end).length,
        0
      )
    : 0;
  const done = workoutsQ.data ? workoutsQ.data.length : 0;
  const entries = weightQ.data || [];
  const weightChange =
    entries.length > 1 ? entries[entries.length - 1].value - entries[0].value : 0;
  const deltaStr =
    weightChange >= 0
      ? `subiste ${weightChange.toFixed(1)} kg`
      : `bajaste ${Math.abs(weightChange).toFixed(1)} kg`;

  return (
    <p className="text-sm">
      Este mes completaste {done} de {planned} entrenos y {deltaStr}.
    </p>
  );
}
