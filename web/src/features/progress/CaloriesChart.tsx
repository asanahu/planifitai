import { useQuery } from '@tanstack/react-query';
import { getSummary } from '../../api/nutrition';
import { today, daysAgo } from '../../utils/date';
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function CaloriesChart() {
  const end = today();
  const start = daysAgo(6);
  const { data } = useQuery({
    queryKey: ['nutrition-summary', start, end],
    queryFn: () => getSummary(start, end),
  });
  return (
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={data || []}>
        <XAxis dataKey="date" hide />
        <YAxis />
        <Tooltip />
        <Bar dataKey="calories" fill="#82ca9d" />
        <Line type="monotone" dataKey="target" stroke="#8884d8" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
