import { useQuery } from '@tanstack/react-query';
import { getDayLog } from '../../api/nutrition';
import { today, daysAgo } from '../../utils/date';
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function CaloriesChart() {
  const end = today();
  const start = daysAgo(6);
  const { data } = useQuery({
    queryKey: ['nutrition-calories-series', start, end],
    queryFn: async () => {
      // Build last 7 days series from day logs to avoid relying on aggregate summary shape
      const days: string[] = [];
      const s = new Date(start);
      const e = new Date(end);
      for (let d = new Date(s); d <= e; d.setDate(d.getDate() + 1)) {
        days.push(d.toISOString().slice(0, 10));
      }
      const entries = await Promise.all(
        days.map(async (d) => {
          try {
            const log = await getDayLog(d);
            return {
              date: d,
              calories: log?.totals?.calories ?? log?.totals?.calories_kcal ?? log?.calories ?? 0,
              target:
                log?.targets?.calories ??
                log?.targets?.calories_target ??
                undefined,
            };
          } catch {
            return { date: d, calories: 0, target: undefined };
          }
        })
      );
      return entries;
    },
  });
  return (
    <div role="img" aria-label="Gráfico de calorías últimos 7 días">
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={Array.isArray(data) ? data : []}>
          <XAxis dataKey="date" hide />
          <YAxis />
          <Tooltip />
          <Bar dataKey="calories" fill="#82ca9d" />
          <Line type="monotone" dataKey="target" stroke="#8884d8" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
