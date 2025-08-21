import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getEntries } from '../../api/progress';
import { getSummary } from '../../api/nutrition';
import { today, daysAgo } from '../../utils/date';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  ResponsiveContainer,
} from 'recharts';
import { Skeleton } from '../../components/ui/Skeleton';

export default function MonthlyProgressChart() {
  const [tab, setTab] = useState<'weight' | 'calories'>('weight');
  const end = today();
  const start = daysAgo(30);
  const weightQ = useQuery({
    queryKey: ['progress', 'weight', start, end],
    queryFn: () => getEntries('weight', start, end),
  });
  const caloriesQ = useQuery({
    queryKey: ['nutrition-summary', start, end],
    queryFn: () => getSummary(start, end),
  });

  if (weightQ.isLoading || caloriesQ.isLoading) {
    return <Skeleton className="h-40" />;
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <button className={`px-2 py-1 text-sm ${tab === 'weight' ? 'font-semibold' : ''}`} onClick={() => setTab('weight')}>
          Peso
        </button>
        <button className={`px-2 py-1 text-sm ${tab === 'calories' ? 'font-semibold' : ''}`} onClick={() => setTab('calories')}>
          Calorías
        </button>
      </div>
      {tab === 'weight' ? (
        <div role="img" aria-label="Progreso de peso mensual">
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={weightQ.data || []}>
              <XAxis dataKey="date" hide />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div role="img" aria-label="Calorías mensuales">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={caloriesQ.data || []}>
              <XAxis dataKey="date" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="calories" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
