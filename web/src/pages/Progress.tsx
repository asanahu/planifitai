import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { addEntry, getEntries, type ProgressEntry } from '../api/progress';
import { today, daysAgo } from '../utils/date';
import WeightChart from '../features/progress/WeightChart';
import CaloriesChart from '../features/progress/CaloriesChart';
import { Skeleton } from '../components/ui/Skeleton';

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
    <div className="space-y-4 p-3 md:p-6">
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
        <button className="h-10 rounded bg-blue-500 px-4 text-white" onClick={() => mutation.mutate()}>
          Guardar peso
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
      <WeightChart />
      <CaloriesChart />
    </div>
  );
}
