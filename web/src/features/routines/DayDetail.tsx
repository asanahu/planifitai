import type { Routine, RoutineDay } from '../../api/routines';
import { completeExercise, uncompleteExercise, addExerciseToDay, completeDay, uncompleteDay, updateRoutineDay } from '../../api/routines';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { pushToast } from '../../components/ui/Toast';
import { useEffect, useMemo, useState } from 'react';
import { generateWorkoutPlanAI } from '../../api/ai';
import { mapAiWorkoutPlanToRoutine } from './aiMap';
import { getExerciseCatalog, getExerciseFilters, getExerciseById } from '../../api/exercises';

interface Props {
  routineId: string;
  day: RoutineDay;
}

function ExerciseRow({
  routineId,
  dayId,
  ex,
  onComplete,
  onUncomplete,
}: {
  routineId: string;
  dayId: string;
  ex: { id: string; name: string; completed: boolean; catalog_id?: string | number; sets?: number; reps?: number; time_seconds?: number; rest_seconds?: number };
  onComplete: (id: string) => void;
  onUncomplete: (id: string) => void;
}) {
  const byId = !!ex.catalog_id;
  const { data: dataById } = useQuery({
    queryKey: ['exercise-demo-id', ex.catalog_id],
    queryFn: () => getExerciseById(ex.catalog_id as string),
    enabled: byId,
  });
  const { data: dataByName } = useQuery({
    queryKey: ['exercise-demo-name', ex.name],
    queryFn: () => getExerciseCatalog({ q: ex.name, limit: 1 }),
    enabled: !byId,
  });
  const first = (byId ? dataById : dataByName?.items?.[0]) as any;
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
      {ex.completed ? (
        <button
          className="text-sm text-red-500"
          onClick={() => onUncomplete(ex.id)}
        >
          Deshacer
        </button>
      ) : (
        <button
          className="text-sm text-blue-500"
          onClick={() => onComplete(ex.id)}
        >
          Completar
        </button>
      )}
    </li>
  );
}

export default function DayDetail({ routineId, day }: Props) {
  const qc = useQueryClient();
  const [showAdder, setShowAdder] = useState(false);
  const [editEquip, setEditEquip] = useState(false);
  const [equipLocal, setEquipLocal] = useState<string[]>(() => (day as any).equipment || []);
  const EQUIPMENT: { key: string; label: string }[] = [
    { key: 'bodyweight', label: 'Peso corporal' },
    { key: 'dumbbells', label: 'Mancuernas' },
    { key: 'barbell', label: 'Barra' },
    { key: 'kettlebell', label: 'Kettlebell' },
    { key: 'bands', label: 'Bandas' },
    { key: 'machine', label: 'Máquinas' },
    { key: 'cable', label: 'Polea' },
  ];
  function toggleEquip(key: string) {
    setEquipLocal((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }
  const saveEquip = useMutation({
    mutationFn: () => updateRoutineDay(routineId, day.id, { equipment: equipLocal }),
    onSuccess: async () => {
      setEditEquip(false);
      pushToast('Material guardado');
      await qc.invalidateQueries({ queryKey: ['routines'] });
    },
    onError: () => pushToast('No se pudo guardar material', 'error'),
  });
  const [q, setQ] = useState('');
  const [muscle, setMuscle] = useState('');
  const [equipment, setEquipment] = useState('');
  const [level, setLevel] = useState('');
  // Prefill equipment filter from day's saved equipment when opening the adder
  useEffect(() => {
    if (!showAdder) return;
    if (equipment) return; // user already chose
    const dayEquip: string[] = ((day as any).equipment || []) as string[];
    const KEY_TO_LABEL: Record<string, string> = {
      bodyweight: 'peso corporal',
      dumbbells: 'mancuernas',
      barbell: 'barra',
      kettlebell: 'kettlebell',
      bands: 'banda elástica',
      machine: 'máquina',
      cable: 'polea',
    };
    for (const k of dayEquip) {
      const label = KEY_TO_LABEL[k];
      if (label) {
        setEquipment(label);
        break;
      }
    }
  }, [showAdder]);
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
    mutationFn: (exerciseId: string) => completeExercise(routineId, day.id, exerciseId, day.date),
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
  const unmut = useMutation({
    mutationFn: (exerciseId: string) => uncompleteExercise(routineId, day.id, exerciseId, day.date),
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
                            e.id === exerciseId ? { ...e, completed: false } : e
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
      pushToast('No se pudo deshacer', 'error');
    },
    onSuccess: () => pushToast('Ejercicio deshecho'),
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
  // Suggest with AI for this day
  const [showSuggest, setShowSuggest] = useState(false);
  const [pendingSuggest, setPendingSuggest] = useState(false);
  const [suggestions, setSuggestions] = useState<{ name: string; reps?: number; sets?: number; time?: number }[]>([]);
  const suggestMut = useMutation({
    mutationFn: async () => {
      const jsIdx = (new Date(day.date).getDay() + 6) % 7; // 0=Mon..6=Sun
      const ai = await generateWorkoutPlanAI({
        days_per_week: 1,
        preferred_days: [jsIdx],
        equipment_by_day: { [jsIdx]: equipLocal.length ? equipLocal : ((day as any).equipment || []) },
      });
      const payload = mapAiWorkoutPlanToRoutine(ai, [jsIdx]);
      const exs = payload.days[0]?.exercises || [];
      setSuggestions(exs);
      setShowSuggest(true);
    },
    onError: () => pushToast('No se pudieron sugerir ejercicios', 'error'),
  });
  return (
    <div className="mt-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">
          {new Date(day.date).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' })}
        </h3>
        <div className="flex gap-2">
          <button
            className="rounded bg-planifit-500 px-3 py-2 text-white text-sm"
            onClick={() => setShowAdder(true)}
          >
            Añadir desde catálogo
          </button>
          <button
            className="rounded border px-3 py-2 text-sm"
            onClick={() => {
              setEditEquip(true);
              setPendingSuggest(true);
            }}
            disabled={suggestMut.isPending}
            title="Selecciona el material y guarda para sugerir"
          >
            {suggestMut.isPending ? 'Sugeriendo…' : 'Sugerir ejercicios (IA)'}
          </button>
          {day.exercises.every((e) => e.completed) ? (
            <button
              className="rounded border px-3 py-2 text-sm"
              onClick={async () => {
                try {
                  await uncompleteDay(routineId, day.id, day.date);
                  pushToast('Se deshizo el día');
                  qc.invalidateQueries({ queryKey: ['routines'] });
                } catch {
                  pushToast('No se pudo deshacer día', 'error');
                }
              }}
            >
              Deshacer día
            </button>
          ) : (
            <button
              className="rounded border px-3 py-2 text-sm"
              onClick={async () => {
                try {
                  await completeDay(routineId, day.id, day.date);
                  pushToast('Día completado');
                  qc.invalidateQueries({ queryKey: ['routines'] });
                } catch {
                  pushToast('No se pudo completar día', 'error');
                }
              }}
            >
              Marcar día completado
            </button>
          )}
        </div>
      </div>
      {(editEquip || (day as any).equipment?.length) && (
        <div className="mb-3 rounded border p-2">
          <div className="text-sm font-medium mb-1">Material del día</div>
          <div className="flex flex-wrap gap-2">
            {EQUIPMENT.map((eq) => (
              <label key={eq.key} className={`px-2 py-1 rounded-full border text-xs cursor-pointer ${equipLocal.includes(eq.key) ? 'bg-planifit-500 text-white border-planifit-500' : 'border-gray-300'}`}>
                <input type="checkbox" className="sr-only" checked={equipLocal.includes(eq.key)} onChange={() => toggleEquip(eq.key)} disabled={!editEquip} />
                {eq.label}
              </label>
            ))}
          </div>
          {editEquip && (
            <div className="mt-2 flex items-center gap-2">
              <button
                className="rounded bg-planifit-500 px-3 py-1 text-white text-sm"
                onClick={async () => {
                  try {
                    // Guarda el material y, si está pendiente, sugiere
                    await saveEquip.mutateAsync();
                    if (pendingSuggest) {
                      await suggestMut.mutateAsync();
                    }
                  } finally {
                    setPendingSuggest(false);
                    setEditEquip(false);
                  }
                }}
                disabled={saveEquip.isPending || suggestMut.isPending}
              >
                {pendingSuggest ? 'Guardar y sugerir (IA)' : 'Guardar material'}
              </button>
              {pendingSuggest && (
                <button
                  className="rounded border px-3 py-1 text-sm"
                  onClick={() => {
                    setPendingSuggest(false);
                    setEditEquip(false);
                    setEquipLocal(((day as any).equipment || []) as string[]);
                  }}
                >
                  Cancelar
                </button>
              )}
            </div>
          )}
        </div>
      )}
      <ul className="space-y-2">
        {day.exercises.map((ex) => (
          <ExerciseRow key={ex.id} routineId={routineId} dayId={day.id} ex={ex} onComplete={(id) => mutation.mutate(id)} onUncomplete={(id) => unmut.mutate(id)} />
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
      {showSuggest && (
        <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-4 shadow-xl dark:bg-gray-900">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">Sugerencias IA</h4>
              <button onClick={() => setShowSuggest(false)} className="text-sm opacity-70">Cerrar</button>
            </div>
            {suggestions.length === 0 ? (
              <div className="p-2 text-sm opacity-80">Sin sugerencias.</div>
            ) : (
              <ul className="space-y-2">
                {suggestions.map((s, i) => (
                  <li key={i} className="flex items-center justify-between rounded border p-2 text-sm">
                    <div className="min-w-0">
                      <div className="font-medium truncate">{s.name}</div>
                      <div className="opacity-70 text-xs">
                        {s.sets && s.reps ? `${s.sets}x${s.reps}` : s.reps ? `${s.reps} reps` : s.sets ? `${s.sets} sets` : ''}
                        {s.time ? ` · ${s.time}s` : ''}
                      </div>
                    </div>
                    <button
                      className="rounded bg-planifit-500 px-2 py-1 text-white"
                      onClick={() => addMut.mutate({ id: `${Date.now()}-${i}`, name: s.name })}
                    >
                      Añadir
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-3 text-right">
              <button
                className="rounded border px-3 py-1 text-sm mr-2"
                onClick={() => setShowSuggest(false)}
              >
                Cerrar
              </button>
              {suggestions.length > 0 && (
                <button
                  className="rounded bg-planifit-500 px-3 py-1 text-white text-sm"
                  onClick={async () => {
                    for (const s of suggestions) {
                      await addMut.mutateAsync({ id: `${Date.now()}-${s.name}`, name: s.name });
                    }
                    setShowSuggest(false);
                  }}
                >
                  Añadir todos
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
