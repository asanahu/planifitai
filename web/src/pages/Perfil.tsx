import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getMe, updateMyProfile, type MeResponse } from '../api/users';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import PageHeader from '../components/layout/PageHeader';
import Overlay from '../components/ui/Overlay';

const schema = z.object({
  age: z.number({ message: 'Edad requerida' }).int().min(14).max(100),
  height_cm: z.number({ message: 'Altura requerida' }).int().min(120).max(220),
  weight_kg: z.number({ message: 'Peso requerido' }).min(30).max(300),
  goal: z.enum(['lose_weight', 'maintain', 'gain_muscle'] as const, { message: 'Objetivo requerido' }),
  activity_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active'] as const, { message: 'Actividad requerida' }),
});

type FormData = z.infer<typeof schema>;

export default function PerfilPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: me, isLoading } = useQuery({ queryKey: ['me'], queryFn: getMe });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isValid } } = useForm<FormData>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: me ? {
      age: me.age ?? undefined,
      height_cm: me.height_cm ?? undefined,
      weight_kg: me.weight_kg ?? undefined,
      goal: (me.goal ?? undefined) as any,
      activity_level: (me.activity_level ?? undefined) as any,
    } : undefined,
  });

  const mutation = useMutation({
    mutationFn: updateMyProfile,
    onSuccess: async (res: MeResponse) => {
      await qc.invalidateQueries({ queryKey: ['me'] });
      if (res.profile_completed) {
        navigate('/hoy');
      }
    },
    onError: (e: any) => setErrorMsg(e?.message || 'Error al guardar'),
  });

  if (isLoading && !me) return <div className="p-4">Cargando…</div>;

  const onSubmit = (data: FormData) => {
    setErrorMsg(null);
    mutation.mutate(data);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-6">
      <PageHeader>
        <h1 className="text-xl font-semibold">Tu perfil</h1>
        <p className="text-sm opacity-90">Completar tu perfil desbloquea PlanifitAI</p>
      </PageHeader>

      <form onSubmit={handleSubmit(onSubmit)} className="relative grid grid-cols-[180px_minmax(0,1fr)] gap-4">
        <label className="self-center" htmlFor="age">Edad</label>
        <div>
          <input id="age" aria-label="Edad" type="number" className="w-full rounded-2xl shadow border p-2" {...register('age', { valueAsNumber: true })} />
          {errors.age && <p className="text-red-500 text-sm">{errors.age.message}</p>}
        </div>

        <label className="self-center" htmlFor="height_cm">Altura (cm)</label>
        <div>
          <input id="height_cm" aria-label="Altura en centímetros" type="number" className="w-full rounded-2xl shadow border p-2" {...register('height_cm', { valueAsNumber: true })} />
          {errors.height_cm && <p className="text-red-500 text-sm">{errors.height_cm.message}</p>}
        </div>

        <label className="self-center" htmlFor="weight_kg">Peso (kg)</label>
        <div>
          <input id="weight_kg" aria-label="Peso en kilogramos" type="number" step="0.1" className="w-full rounded-2xl shadow border p-2" {...register('weight_kg', { valueAsNumber: true })} />
          {errors.weight_kg && <p className="text-red-500 text-sm">{errors.weight_kg.message}</p>}
        </div>

        <label className="self-center" htmlFor="goal">Objetivo</label>
        <div>
          <select id="goal" aria-label="Objetivo" className="w-full rounded-2xl shadow border p-2" defaultValue="" {...register('goal')}>
            <option value="" disabled>Selecciona tu objetivo</option>
            <option value="lose_weight">Perder peso</option>
            <option value="maintain">Mantener</option>
            <option value="gain_muscle">Ganar músculo</option>
          </select>
          {errors.goal && <p className="text-red-500 text-sm">{errors.goal.message}</p>}
        </div>

        <label className="self-center" htmlFor="activity_level">Actividad</label>
        <div>
          <select id="activity_level" aria-label="Nivel de actividad" className="w-full rounded-2xl shadow border p-2" defaultValue="" {...register('activity_level')}>
            <option value="" disabled>Selecciona tu actividad</option>
            <option value="sedentary">Sedentario</option>
            <option value="light">Ligera</option>
            <option value="moderate">Moderada</option>
            <option value="active">Activa</option>
            <option value="very_active">Muy activa</option>
          </select>
          {errors.activity_level && <p className="text-red-500 text-sm">{errors.activity_level.message}</p>}
        </div>

        <div />
        <div className="flex items-center gap-3">
          <button type="submit" disabled={!isValid || mutation.isPending} className="bg-planifit-500 disabled:opacity-50 text-white px-4 py-2 rounded-2xl shadow">
            {mutation.isPending ? 'Guardando…' : 'Guardar'}
          </button>
          {errorMsg && <span className="text-red-600 text-sm">{errorMsg}</span>}
        </div>
        {mutation.isPending && <Overlay>Guardando tu perfil…</Overlay>}
      </form>
    </div>
  );
}
