import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { generateWorkoutPlanAI } from '../../api/ai';
import { mapAiWorkoutPlanToRoutine } from './aiMap';
import { createRoutine, setActiveRoutine, type RoutineCreatePayload, listRoutines, createNextWeekRoutine, deleteRoutine } from '../../api/routines';
import { pushToast } from '../../components/ui/Toast';
import Overlay from '../../components/ui/Overlay';

const WEEKDAYS = [
  { id: 0, label: 'Lunes' },
  { id: 1, label: 'Martes' },
  { id: 2, label: 'Miércoles' },
  { id: 3, label: 'Jueves' },
  { id: 4, label: 'Viernes' },
  { id: 5, label: 'Sábado' },
  { id: 6, label: 'Domingo' },
];

export default function GenerateFromAI() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const useAI = import.meta.env.VITE_FEATURE_AI === '1';
  const [selectedDays, setSelectedDays] = useState<number[]>([0, 2, 4]);
  const [injuries, setInjuries] = useState<string>('');
  const [equipmentByDay, setEquipmentByDay] = useState<Record<number, string[]>>({});

  const EQUIPMENT: { key: string; label: string }[] = [
    { key: 'bodyweight', label: 'Peso corporal' },
    { key: 'dumbbells', label: 'Mancuernas' },
    { key: 'barbell', label: 'Barra' },
    { key: 'kettlebell', label: 'Kettlebell' },
    { key: 'bands', label: 'Bandas' },
    { key: 'machine', label: 'Máquinas' },
    { key: 'cable', label: 'Polea' },
  ];

  function toggleEquip(day: number, key: string) {
    setEquipmentByDay((prev) => {
      const curr = new Set(prev[day] || []);
      if (curr.has(key)) curr.delete(key);
      else curr.add(key);
      return { ...prev, [day]: Array.from(curr) };
    });
  }

  // Prefill from current routine if exists (one-time, non-blocking for edits)
  const routinesQ = useQuery({ queryKey: ['routines'], queryFn: listRoutines });
  const [prefilled, setPrefilled] = useState(false);
  useEffect(() => {
    if (prefilled) return;
    const routines = routinesQ.data || [];
    if (routines.length === 0) return;
    // Only prefill if user hasn't edited yet: still defaults and no equipment set
    const isDefaultDays = selectedDays.join(',') === '0,2,4';
    const hasEquip = Object.keys(equipmentByDay || {}).length > 0;
    if (!isDefaultDays || hasEquip) return;
    const r = routines[routines.length - 1];
    const days = r.days || [];
    const wk: number[] = days.map((d) => (new Date(d.date).getDay() + 6) % 7);
    if (wk.length > 0) setSelectedDays(Array.from(new Set(wk)).sort((a, b) => a - b));
    // Extract equipment per day if present
    const byDay: Record<number, string[]> = {};
    for (const d of days) {
      const jsIdx = (new Date(d.date).getDay() + 6) % 7;
      const eq = (d as any).equipment as string[] | undefined;
      if (eq && eq.length) byDay[jsIdx] = eq;
    }
    if (Object.keys(byDay).length > 0) setEquipmentByDay(byDay);
    setPrefilled(true);
  }, [prefilled, routinesQ.data]);

  const fallback: RoutineCreatePayload = {
    name: 'Full Body 3d',
    days: [0, 2, 4].map((weekday) => ({
      weekday,
      name: 'Full Body',
      duration: 60,
      exercises: [{ name: 'Push Ups', reps: 10, time: 60 }],
    })),
  };

  const mutation = useMutation({
    mutationFn: async () => {
      try {
        // 1) Reset: borrar todas las rutinas existentes para evitar solapes de semanas
        try {
          const existing = await listRoutines();
          await Promise.allSettled(existing.map((r) => deleteRoutine(r.id)));
        } catch {
          // continuar aunque falle alguna
        }

        if (!useAI) throw new Error('disabled');
        const ai = await generateWorkoutPlanAI({
          days_per_week: selectedDays.length || 3,
          preferred_days: selectedDays,
          equipment_by_day: equipmentByDay,
          injuries: injuries
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
        });
        const payload = mapAiWorkoutPlanToRoutine(ai, selectedDays, equipmentByDay);
        const routine = await createRoutine(payload);
        await setActiveRoutine(routine.id);
        return routine;
      } catch {
        // fallback respetando días seleccionados
        const fb = {
          ...fallback,
          days: (selectedDays.length ? selectedDays : [0, 2, 4]).map((weekday) => ({
            weekday,
            name: 'Full Body',
            duration: 60,
            exercises: [{ name: 'Push Ups', reps: 10, time: 60 }],
          })),
        } satisfies RoutineCreatePayload;
        // Intentamos borrar antes también en fallback
        try {
          const existing = await listRoutines();
          await Promise.allSettled(existing.map((r) => deleteRoutine(r.id)));
        } catch {}
        const routine = await createRoutine(fb);
        pushToast('Usando rutina por defecto', 'error');
        return routine;
      }
    },
    onSuccess: async (routine) => {
      qc.invalidateQueries({ queryKey: ['routines'] });
      qc.invalidateQueries({ queryKey: ['routine', routine.id] });
      pushToast('Rutina generada');
      // Siempre preparamos la siguiente semana tras generar
      try {
        await createNextWeekRoutine(routine.id);
        qc.invalidateQueries({ queryKey: ['routines'] });
        pushToast('Siguiente semana preparada');
      } catch {
        // opcional, ignorar si falla
      }
      navigate('/workout');
    },
    onError: () => pushToast('No se pudo generar rutina', 'error'),
  });

  return (
    <div className="relative space-y-4">
      <div className="space-y-2">
        <div>
          <p className="text-sm opacity-80 mb-1">¿Qué días quieres entrenar?</p>
          <div className="flex gap-2 flex-wrap">
            {WEEKDAYS.map((d) => (
              <label key={d.id} className={`px-3 py-1 rounded-full border cursor-pointer ${selectedDays.includes(d.id) ? 'bg-planifit-500 text-white border-planifit-500' : 'border-gray-300'}`}>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={selectedDays.includes(d.id)}
                  onChange={(e) => {
                    setSelectedDays((prev) => (
                      e.target.checked ? [...prev, d.id] : prev.filter((x) => x !== d.id)
                    ).sort((a, b) => a - b));
                  }}
                />
                {d.label}
              </label>
            ))}
          </div>
        </div>
        {selectedDays.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm opacity-80">Material disponible por día</p>
            <div className="grid gap-2">
              {selectedDays.map((d) => (
                <div key={d} className="rounded border p-2">
                  <div className="text-sm font-medium mb-1">{WEEKDAYS.find((w) => w.id === d)?.label}</div>
                  <div className="flex flex-wrap gap-2">
                    {EQUIPMENT.map((eq) => (
                      <label key={eq.key} className={`px-2 py-1 rounded-full border text-xs cursor-pointer ${equipmentByDay[d]?.includes(eq.key) ? 'bg-planifit-500 text-white border-planifit-500' : 'border-gray-300'}`}>
                        <input
                          type="checkbox"
                          className="sr-only"
                          checked={!!equipmentByDay[d]?.includes(eq.key)}
                          onChange={() => toggleEquip(d, eq.key)}
                        />
                        {eq.label}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <div>
          <label className="block text-sm opacity-80 mb-1">Lesiones o restricciones (separadas por coma)</label>
          <input
            type="text"
            value={injuries}
            onChange={(e) => setInjuries(e.target.value)}
            placeholder="p. ej. hombro derecho, rodilla"
            className="w-full rounded-md border border-gray-300 p-2"
          />
        </div>
      </div>

      <button className="btn" disabled={mutation.isPending} onClick={() => mutation.mutate()}>
        {mutation.isPending ? 'Generando rutina…' : 'Generar plan IA'}
      </button>
      {mutation.isPending && <Overlay>Tu rutina se está generando; analizando tu perfil, material disponible y lesiones, puede tardar unos minutos... ¡No cierres esta ventana!</Overlay>}
    </div>
  );
}
