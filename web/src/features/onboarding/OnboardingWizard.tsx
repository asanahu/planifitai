import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { createProfile, updateProfile, getProfile } from '../../api/profile';
import { generateWorkoutPlanAI } from '../../api/ai';
import { mapAiWorkoutPlanToRoutine } from '../routines/aiMap';
import { createRoutine, setActiveRoutine, cloneTemplate } from '../../api/routines';
import { pushToast } from '../../components/ui/Toast';
import { useNavigate, Link } from 'react-router-dom';

const profileSchema = z.object({
  age: z.number().min(1),
  height: z.number().min(1),
  weight: z.number().min(1),
  goal: z.string().min(1),
  activity: z.string().min(1),
});

type ProfileData = z.infer<typeof profileSchema>;

export function OnboardingWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: getProfile });

  const form = useForm<ProfileData>({
    resolver: zodResolver(profileSchema),
    defaultValues: profile ?? { age: 0, height: 0, weight: 0, goal: '', activity: '' },
  });

  const saveProfile = async (data: ProfileData) => {
    try {
      if (profile) await updateProfile(profile.id, data);
      else await createProfile(data);
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
          <input type="number" placeholder="Altura" {...form.register('height', { valueAsNumber: true })} className="w-full border p-2" />
          <input type="number" placeholder="Peso" {...form.register('weight', { valueAsNumber: true })} className="w-full border p-2" />
          <input placeholder="Objetivo" {...form.register('goal')} className="w-full border p-2" />
          <input placeholder="Actividad" {...form.register('activity')} className="w-full border p-2" />
          <button type="submit" className="rounded bg-blue-500 px-4 py-2 text-white">Guardar y continuar</button>
        </form>
        <Link to="/today?skip=1" className="text-sm text-blue-500">
          Saltar por ahora
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-lg font-semibold">Paso 2: Crea tu plan</h1>
      <button onClick={createPlan} className="rounded bg-green-500 px-4 py-2 text-white">
        {import.meta.env.VITE_FEATURE_AI === '1' ? 'Generar con IA' : 'Usar plantilla por defecto'}
      </button>
      <Link to="/today?skip=1" className="block text-sm text-blue-500">
        Saltar por ahora
      </Link>
    </div>
  );
}

export default OnboardingWizard;

