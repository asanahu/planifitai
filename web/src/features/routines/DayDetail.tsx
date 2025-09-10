import type { Routine, RoutineDay } from '../../api/routines';
import { completeExercise, addExerciseToDay } from '../../api/routines';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { pushToast } from '../../components/ui/Toast';
import { useMemo, useState } from 'react';
import { getExerciseCatalog, getExerciseFilters } from '../../api/exercises';

interface Props {
  routineId: string;
  day: RoutineDay;
}

function ExerciseRow({
  routineId,
  dayId,
  ex,
  onComplete,
}: {
  routineId: string;
  dayId: string;
  ex: { id: string; name: string; completed: boolean; sets?: number; reps?: number; time_seconds?: number; rest_seconds?: number };
  onComplete: (id: string) => void;
}) {
  const { data } = useQuery({
    queryKey: ['exercise-demo', ex.name],
    queryFn: () => getExerciseCatalog({ q: ex.name, limit: 1 }),
  });
  const first = data?.items?.[0];
  const demoUrl = first?.demo_url || null;
  return (
    <li key={ex.id} className="flex items-center justify-between rounded border p-2 gap-3">
      <div className="flex items-start gap-3 min-w-0">
        {demoUrl ? (
          <img src={demoUrl} alt={ex.name} className="w-14 h-14 object-cover rounded" />
        ) : (
          <div className="w-14 h-14 rounded bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-[10px] opacity-70">
            Sin demo
          </div>
        )}
        <div className="min-w-0">
          <div className="truncate font-medium">{ex.name}</div>
          <div className="text-[11px] opacity-80">
            {(() => {
              const parts: string[] = [];
              if (ex.sets && ex.reps) parts.push(`${ex.sets}x${ex.reps}`);
              else if (ex.sets) parts.push(`${ex.sets} series`);
              if (ex.time_seconds) parts.push(`${ex.time_seconds}s`);
              if (ex.rest_seconds) parts.push(`rest ${ex.rest_seconds}s`);
              return parts.join(' · ');
            })()}
          </div>
          {first?.description && (
            <div className="text-[11px] opacity-70 line-clamp-2 mt-0.5">{first.description}</div>
          )}
        </div>
      </div>
      <button
        className="text-sm text-blue-500 disabled:opacity-50"
        disabled={ex.completed}
        onClick={() => onComplete(ex.id)}
      >
        {ex.completed ? 'Done' : 'Complete'}
      </button>
    </li>
  );
}

export default function DayDetail({ routineId, day }: Props) {
  const qc = useQueryClient();
  const [showAdder, setShowAdder] = useState(false);
  const [q, setQ] = useState('');
  const [muscle, setMuscle] = useState('');
  const [equipment, setEquipment] = useState('');
  const [level, setLevel] = useState('');
  const params = useMemo(
    () => ({
      q: q || undefined,
      muscle: muscle || undefined,
      equipment: equipment || undefined,
      level: level || undefined,
      limit: 12,
      offset: 0,
    }),
    [q, muscle, equipment, level]
  );
  const catalogQ = useQuery({
    queryKey: ['exercise-catalog-inline', params],
    queryFn: () => getExerciseCatalog(params),
    enabled: showAdder,
  });
  const filtersQ = useQuery({ queryKey: ['exercise-filters'], queryFn: getExerciseFilters, enabled: showAdder });
  const mutation = useMutation({
    mutationFn: (exerciseId: string) => completeExercise(routineId, day.id, exerciseId),
    onMutate: async (exerciseId) => {
      await qc.cancelQueries({ queryKey: ['routines'] });
      const prev = qc.getQueryData<Routine[]>(['routines']);
      qc.setQueryData<Routine[]>(
        ['routines'],
        (old) =>
          old?.map((r) =>
            r.id === routineId
              ? {
                  ...r,
                  days: r.days.map((d) =>
                    d.id === day.id
                      ? {
                          ...d,
                          exercises: d.exercises.map((e) =>
                            e.id === exerciseId ? { ...e, completed: true } : e
                          ),
                        }
                      : d
                  ),
                }
              : r
          ) ?? old
      );
      return { prev };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.prev) qc.setQueryData(['routines'], ctx.prev);
      pushToast('Error al completar', 'error');
    },
    onSuccess: () => pushToast('Ejercicio completado'),
    onSettled: () => qc.invalidateQueries({ queryKey: ['routines'] }),
  });
  const addMut = useMutation({
    mutationFn: (payload: { id: string | number; name: string }) =>
      addExerciseToDay(routineId, day.id, { exercise_name: payload.name, exercise_id: payload.id, sets: 3, reps: 10 }),
    onSuccess: async () => {
      pushToast('Ejercicio añadido');
      await qc.invalidateQueries({ queryKey: ['routines'] });
    },
    onError: (e: any) => pushToast(e?.message || 'No se pudo añadir', 'error'),
  });
  return (
    <div className="mt-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">{new Date(day.date).toDateString()}</h3>
        <button
          className="rounded bg-planifit-500 px-3 py-2 text-white text-sm"
          onClick={() => setShowAdder(true)}
        >
          Añadir desde catálogo
        </button>
      </div>
      <ul className="space-y-2">
        {day.exercises.map((ex) => (
          <ExerciseRow key={ex.id} routineId={routineId} dayId={day.id} ex={ex} onComplete={(id) => mutation.mutate(id)} />
        ))}
      </ul>

      {showAdder && (
        <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-4 shadow-xl dark:bg-gray-900">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">Añadir ejercicio</h4>
              <button onClick={() => setShowAdder(false)} className="text-sm opacity-70">Cerrar</button>
            </div>
            <div className="mb-3 grid grid-cols-1 md:grid-cols-4 gap-2">
              <input
                placeholder="Nombre"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="rounded border p-2"
              />
              <select value={muscle} onChange={(e) => setMuscle(e.target.value)} className="rounded border p-2">
                <option value="">Músculo</option>
                {filtersQ.data?.muscles?.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <select value={equipment} onChange={(e) => setEquipment(e.target.value)} className="rounded border p-2">
                <option value="">Equipo</option>
                {filtersQ.data?.equipment?.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <select value={level} onChange={(e) => setLevel(e.target.value)} className="rounded border p-2">
                <option value="">Nivel</option>
                <option value="beginner">Principiante</option>
                <option value="intermediate">Intermedio</option>
                <option value="expert">Experto</option>
              </select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[60vh] overflow-auto">
              {catalogQ.isLoading && <div className="p-2">Cargando…</div>}
              {catalogQ.data?.items?.map((item) => (
                <div key={`${item.id}`} className="rounded border p-2 space-y-2">
                  <div className="flex items-start gap-3">
                    {item.demo_url ? (
                      <img src={item.demo_url} alt={item.name} className="w-16 h-16 object-cover rounded" />
                    ) : (
                      <div className="w-16 h-16 rounded bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-[10px] opacity-70">Sin demo</div>
                    )}
                    <div className="min-w-0">
                      <div className="font-medium truncate">{item.name}</div>
                      <div className="text-xs opacity-70 truncate">{item.muscle_groups?.join(', ') || '—'}</div>
                    </div>
                  </div>
                  <button
                    className="w-full rounded bg-planifit-500 px-3 py-2 text-white text-sm disabled:opacity-50"
                    disabled={addMut.isPending}
                    onClick={() => addMut.mutate({ id: item.id, name: item.name })}
                  >
                    Añadir a este día
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
