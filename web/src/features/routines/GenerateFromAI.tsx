import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { generateWorkoutPlanAI } from '../../api/ai';
import { mapAiWorkoutPlanToRoutine } from './aiMap';
import { createRoutine, setActiveRoutine, type RoutineCreatePayload } from '../../api/routines';
import { pushToast } from '../../components/ui/Toast';
import Overlay from '../../components/ui/Overlay';

const WEEKDAYS = [
  { id: 0, label: 'Lun' },
  { id: 1, label: 'Mar' },
  { id: 2, label: 'Mié' },
  { id: 3, label: 'Jue' },
  { id: 4, label: 'Vie' },
  { id: 5, label: 'Sáb' },
  { id: 6, label: 'Dom' },
];

export default function GenerateFromAI() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const useAI = import.meta.env.VITE_FEATURE_AI === '1';
  const [selectedDays, setSelectedDays] = useState<number[]>([0, 2, 4]);
  const [injuries, setInjuries] = useState<string>('');

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
        if (!useAI) throw new Error('disabled');
        const ai = await generateWorkoutPlanAI({
          days_per_week: selectedDays.length || 3,
          preferred_days: selectedDays,
          injuries: injuries
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
        });
        const payload = mapAiWorkoutPlanToRoutine(ai, selectedDays);
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
        const routine = await createRoutine(fb);
        pushToast('Usando rutina por defecto', 'error');
        return routine;
      }
    },
    onSuccess: (routine) => {
      qc.invalidateQueries({ queryKey: ['routines'] });
      qc.invalidateQueries({ queryKey: ['routine', routine.id] });
      pushToast('Rutina generada');
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
      {mutation.isPending && <Overlay>Tu rutina se está generando; puede tardar unos segundos…</Overlay>}
    </div>
  );
}
