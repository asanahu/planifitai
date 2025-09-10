import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { getExerciseCatalog, getExerciseFilters, type ExerciseItem } from '../api/exercises';
import Card from '../components/ui/card';
import PageHeader from '../components/layout/PageHeader';
import { getUserRoutines, addExerciseToDay } from '../api/routines';
import { pushToast } from '../components/ui/Toast';

function ExerciseCard({ ex }: { ex: ExerciseItem }) {
  return (
    <div className="rounded-2xl border p-3 flex gap-3 items-start">
      {ex.demo_url ? (
        <img src={ex.demo_url} alt={ex.name} className="w-24 h-24 object-cover rounded" />
      ) : (
        <div className="w-24 h-24 rounded bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-xs opacity-70">
          Sin demo
        </div>
      )}
      <div className="min-w-0">
        <div className="font-semibold truncate">{ex.name}</div>
        <div className="text-sm opacity-80 truncate">
          {ex.muscle_groups?.length ? ex.muscle_groups.join(', ') : '—'}
        </div>
        <div className="text-xs opacity-70 mt-1">
          {ex.equipment || 'sin equipo'}{ex.level ? ` · ${ex.level}` : ''}
        </div>
      </div>
    </div>
  );
}

export default function ExerciseCatalogPage() {
  const [q, setQ] = useState('');
  const [muscle, setMuscle] = useState('');
  const [equipment, setEquipment] = useState('');
  const [level, setLevel] = useState('');
  const [routineId, setRoutineId] = useState<string>('');
  const [dayId, setDayId] = useState<string>('');
  const qc = useQueryClient();

  const params = useMemo(() => ({
    q: q || undefined,
    muscle: muscle || undefined,
    equipment: equipment || undefined,
    level: level || undefined,
    limit: 50,
    offset: 0,
  }), [q, muscle, equipment, level]);

  const { data, isLoading } = useQuery({
    queryKey: ['exercise-catalog', params],
    queryFn: () => getExerciseCatalog(params),
  });
  const filtersQ = useQuery({ queryKey: ['exercise-filters'], queryFn: getExerciseFilters });
  const routinesQ = useQuery({ queryKey: ['routines'], queryFn: getUserRoutines });

  const addMutation = useMutation({
    mutationFn: (ex: ExerciseItem) => {
      if (!routineId || !dayId) throw new Error('Selecciona rutina y día');
      return addExerciseToDay(routineId, dayId, { exercise_name: ex.name, exercise_id: ex.id, sets: 3, reps: 10 });
    },
    onSuccess: async () => {
      pushToast('Ejercicio añadido');
      await qc.invalidateQueries({ queryKey: ['routines'] });
    },
    onError: (e: any) => pushToast(e?.message || 'No se pudo añadir', 'error'),
  });

  return (
    <div className="mx-auto max-w-5xl p-4 space-y-4">
      <PageHeader>
        <h1 className="text-xl font-semibold">Catálogo de ejercicios</h1>
        <p className="text-sm opacity-90">Busca por nombre, músculo, equipo o nivel</p>
      </PageHeader>

      <Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            placeholder="Buscar (nombre)"
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
            <option value="">Nivel (cualquiera)</option>
            <option value="beginner">Principiante</option>
            <option value="intermediate">Intermedio</option>
            <option value="expert">Experto</option>
          </select>
        </div>
      </Card>

      <Card>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
          <select value={routineId} onChange={(e) => { setRoutineId(e.target.value); setDayId(''); }} className="rounded border p-2">
            <option value="">Selecciona rutina (opcional)</option>
            {routinesQ.data?.map((r: any) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
          <select value={dayId} onChange={(e) => setDayId(e.target.value)} className="rounded border p-2" disabled={!routineId}>
            <option value="">Día</option>
            {routinesQ.data?.find((r: any) => String(r.id) === String(routineId))?.days?.map((d: any) => (
              <option key={d.id} value={d.id}>
                {typeof d.weekday === 'number' ? ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][d.weekday] : (d.date || d.id)}
              </option>
            ))}
          </select>
          <div className="text-sm opacity-70">
            Selecciona rutina y día para poder añadir ejercicios desde el catálogo.
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {isLoading && <div className="p-4">Cargando…</div>}
        {data?.items?.map((ex) => (
          <div key={`${ex.id}`} className="space-y-2">
            <ExerciseCard ex={ex} />
            <button
              className="w-full rounded bg-planifit-500 px-3 py-2 text-white disabled:opacity-50"
              disabled={!routineId || !dayId || addMutation.isPending}
              onClick={() => addMutation.mutate(ex)}
            >
              Añadir a día
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
