import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createProgressEntry, listProgress } from '../../api/progress';
import { daysAgo, today } from '../../utils/date';
import { pushToast } from '../../components/ui/Toast';
import { Skeleton } from '../../components/ui/Skeleton';

export function QuickWeighCard() {
  const date = today();
  const [value, setValue] = useState('');
  const progressQuery = useQuery({
    queryKey: ['weight', date],
    queryFn: () => listProgress({ metric: 'weight', start: daysAgo(30), end: date }),
  });
  const mutation = useMutation({
    mutationFn: (v: number) => createProgressEntry({ metric: 'weight', date, value: v }),
    onSuccess: () => {
      pushToast('Peso guardado');
      setValue('');
      progressQuery.refetch();
    },
    onError: () => pushToast('Error al guardar', 'error'),
  });

  if (progressQuery.isLoading) {
    return <Skeleton className="h-32" />;
  }

  const entries = progressQuery.data ?? [];
  const last = entries[entries.length - 1];
  const delta7 = last && entries.length > 1 ? last.value - entries[Math.max(0, entries.length - 7)].value : 0;

  return (
    <section className="border p-4 rounded space-y-2">
      <h2 className="font-bold">Peso rápido</h2>
      {last && (
        <p className="text-sm text-gray-600">Último: {last.value}kg (Δ7d {delta7.toFixed(1)})</p>
      )}
      <div className="flex space-x-2">
        <input
          type="number"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="border p-2 flex-1"
          placeholder="kg"
        />
        <button
          onClick={() => mutation.mutate(parseFloat(value))}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Guardar
        </button>
      </div>
    </section>
  );
}
