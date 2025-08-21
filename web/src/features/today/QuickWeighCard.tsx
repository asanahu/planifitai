import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createProgressEntry, listProgress, type ProgressEntry } from '../../api/progress';
import { daysAgo, today } from '../../utils/date';
import { pushToast } from '../../components/ui/Toast';
import { Skeleton } from '../../components/ui/Skeleton';
import { Link } from 'react-router-dom';
import { Scale } from 'lucide-react';

export function QuickWeighCard() {
  const date = today();
  const qc = useQueryClient();
  const [value, setValue] = useState('');
  const progressQuery = useQuery({
    queryKey: ['weight', date],
    queryFn: () => listProgress({ metric: 'weight', start: daysAgo(30), end: date }),
  });
  const mutation = useMutation({
    mutationFn: (v: number) => createProgressEntry({ metric: 'weight', date, value: v }),
    onMutate: async (v) => {
      await qc.cancelQueries({ queryKey: ['weight', date] });
      const prev = qc.getQueryData<ProgressEntry[]>(['weight', date]) ?? [];
      qc.setQueryData<ProgressEntry[]>(['weight', date], [
        ...prev,
        { id: 'temp', metric: 'weight', date, value: v },
      ]);
      setValue('');
      return { prev };
    },
    onError: (_err, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(['weight', date], ctx.prev as ProgressEntry[]);
      pushToast('Error al guardar', 'error');
    },
    onSuccess: () => pushToast('Peso guardado'),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['weight'] });
      qc.invalidateQueries({ queryKey: ['progress', 'weight'] });
    },
  });

  if (progressQuery.isLoading) {
    return <Skeleton className="h-40" />;
  }

  const entries = progressQuery.data ?? [];
  const last = entries[entries.length - 1];
  const delta7 =
    last && entries.length > 1 ? last.value - entries[Math.max(0, entries.length - 7)].value : 0;

  return (
    <section className="space-y-3 rounded border bg-white p-3 shadow-sm dark:bg-gray-800">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        <Scale className="h-5 w-5" /> Peso rápido
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        Un registro hoy te acerca a tu objetivo
      </p>
      {last && (
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Último: {last.value}kg (Δ7d {delta7.toFixed(1)})
        </p>
      )}
      <div className="flex items-center gap-2">
        <label htmlFor="quick-weight" className="sr-only">
          Peso en kilogramos
        </label>
        <input
          id="quick-weight"
          type="number"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="flex-1 rounded border p-2"
          placeholder="kg"
        />
        <button
          onClick={() => mutation.mutate(parseFloat(value))}
          className="h-10 rounded bg-blue-500 px-4 text-white"
        >
          Guardar
        </button>
      </div>
      <div className="text-right">
        <Link className="text-sm text-blue-500" to="/progress">
          Ver progreso
        </Link>
      </div>
    </section>
  );
}
