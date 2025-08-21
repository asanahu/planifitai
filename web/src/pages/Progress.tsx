import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { addEntry, getEntries } from '../api/progress';
import { today, daysAgo } from '../utils/date';
import WeightChart from '../features/progress/WeightChart';
import CaloriesChart from '../features/progress/CaloriesChart';

export default function ProgressPage() {
  const qc = useQueryClient();
  const [value, setValue] = useState('');
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
  return (
    <div className="space-y-4 p-4">
      <div className="space-x-2">
        <input className="border p-1" type="number" value={value} onChange={(e) => setValue(e.target.value)} />
        <button className="btn" onClick={() => mutation.mutate()}>Guardar peso</button>
      </div>
      <ul>
        {entriesQuery.data?.map((e: any) => (
          <li key={e.id}>{e.date}: {e.value}kg</li>
        ))}
      </ul>
      <WeightChart />
      <CaloriesChart />
    </div>
  );
}
