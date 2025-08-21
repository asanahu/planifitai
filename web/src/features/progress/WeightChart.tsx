import { useQuery } from '@tanstack/react-query';
import { getEntries } from '../../api/progress';
import { today, daysAgo } from '../../utils/date';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function WeightChart() {
  const end = today();
  const start = daysAgo(30);
  const { data } = useQuery({
    queryKey: ['progress', 'weight', start, end],
    queryFn: () => getEntries('weight', start, end),
  });
  return (
    <div role="img" aria-label="Gráfico de peso últimos 30 días">
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data || []}>
          <XAxis dataKey="date" hide />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
