import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { getMe, updateMyProfile } from '../../api/users';
import { generateWorkoutPlanAI } from '../../api/ai';
import { mapAiWorkoutPlanToRoutine } from '../routines/aiMap';
import { createRoutine, setActiveRoutine, cloneTemplate } from '../../api/routines';
import { pushToast } from '../../components/ui/Toast';
import { useNavigate, Link } from 'react-router-dom';

const profileSchema = z.object({
  age: z.number().int().min(14).max(100),
  height_cm: z.number().int().min(120).max(220),
  weight_kg: z.number().min(30).max(300),
  goal: z.enum(['lose_weight', 'maintain', 'gain_muscle'] as const),
  activity_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active'] as const),
});

type ProfileData = z.infer<typeof profileSchema>;

export function OnboardingWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const { data: me } = useQuery({ queryKey: ['me'], queryFn: getMe });

  const form = useForm<ProfileData>({
    resolver: zodResolver(profileSchema),
    defaultValues: me
      ? {
          age: (me.age ?? 0) as number,
          height_cm: (me.height_cm ?? 0) as number,
          weight_kg: (me.weight_kg ?? 0) as number,
          goal: (me.goal ?? undefined) as any,
          activity_level: (me.activity_level ?? undefined) as any,
        }
      : undefined,
  });

  const saveProfile = async (data: ProfileData) => {
    try {
      await updateMyProfile(data);
      setStep(2);
    } catch {
      pushToast('No se pudo guardar perfil', 'error');
    }
  };

  const createPlan = async () => {
    try {
      if (import.meta.env.VITE_FEATURE_AI === '1') {
        const ai = await generateWorkoutPlanAI();
        const payload = mapAiWorkoutPlanToRoutine(ai);
        const routine = await createRoutine(payload);
        await setActiveRoutine(routine.id);
      } else {
        const routine = await cloneTemplate(import.meta.env.VITE_FALLBACK_TEMPLATE_ID);
        await setActiveRoutine(routine.id);
      }
      pushToast('Plan creado');
      navigate('/today');
    } catch {
      try {
        const routine = await cloneTemplate(import.meta.env.VITE_FALLBACK_TEMPLATE_ID);
        await setActiveRoutine(routine.id);
        pushToast('Plan por defecto creado');
        navigate('/today');
      } catch {
        pushToast('No se pudo crear plan', 'error');
      }
    }
  };

  if (step === 1) {
    return (
      <div className="space-y-4 p-4">
        <h1 className="text-lg font-semibold">Paso 1: Completa tu perfil</h1>
        <form onSubmit={form.handleSubmit(saveProfile)} className="space-y-2 max-w-md">
          <input type="number" placeholder="Edad" {...form.register('age', { valueAsNumber: true })} className="w-full border p-2" />
          <input type="number" placeholder="Altura (cm)" {...form.register('height_cm', { valueAsNumber: true })} className="w-full border p-2" />
          <input type="number" placeholder="Peso (kg)" step="0.1" {...form.register('weight_kg', { valueAsNumber: true })} className="w-full border p-2" />
          <select {...form.register('goal')} className="w-full border p-2" defaultValue="">
            <option value="" disabled>Objetivo</option>
            <option value="lose_weight">Perder peso</option>
            <option value="maintain">Mantener</option>
            <option value="gain_muscle">Ganar músculo</option>
          </select>
          <select {...form.register('activity_level')} className="w-full border p-2" defaultValue="">
            <option value="" disabled>Actividad</option>
            <option value="sedentary">Sedentario</option>
            <option value="light">Ligera</option>
            <option value="moderate">Moderada</option>
            <option value="active">Activa</option>
            <option value="very_active">Muy activa</option>
          </select>
          <button
            type="submit"
            className="rounded bg-blue-500 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Guardar y continuar"
          >
            Guardar y continuar
          </button>
        </form>
        <Link
          to="/today?skip=1"
          role="button"
          aria-label="Saltar por ahora"
          className="text-sm text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Saltar por ahora
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-lg font-semibold">Paso 2: Crea tu plan</h1>
      <button
        onClick={createPlan}
        className="rounded bg-green-500 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
        aria-label={
          import.meta.env.VITE_FEATURE_AI === '1'
            ? 'Generar con IA'
            : 'Usar plantilla por defecto'
        }
      >
        {import.meta.env.VITE_FEATURE_AI === '1'
          ? 'Generar con IA'
          : 'Usar plantilla por defecto'}
      </button>
      <Link
        to="/today?skip=1"
        role="button"
        aria-label="Saltar por ahora"
        className="block text-sm text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        Saltar por ahora
      </Link>
    </div>
  );
}

export default OnboardingWizard;

