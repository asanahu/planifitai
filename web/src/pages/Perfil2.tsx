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
  first_name: z.string().min(1).max(50).optional(),
  last_name: z.string().min(1).max(50).optional(),
  sex: z.enum(['male', 'female', 'other'] as const).optional(),
  age: z.number({ message: 'Edad requerida' }).int().min(14).max(100),
  height_cm: z.number({ message: 'Altura requerida' }).int().min(120).max(220),
  weight_kg: z.number({ message: 'Peso requerido' }).min(30).max(300),
  goal: z.enum(['lose_weight', 'maintain', 'gain_muscle'] as const, { message: 'Objetivo requerido' }),
  activity_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active'] as const, { message: 'Actividad requerida' }),
  training_days_per_week: z.number().int().min(0).max(7).optional(),
  time_per_session_min: z.number().int().min(10).max(240).optional(),
  equipment_access: z.enum(['none', 'basic', 'full_gym'] as const).optional(),
  dietary_preference: z.enum(['omnivore', 'vegetarian', 'vegan', 'pescatarian', 'keto', 'none'] as const).optional(),
  allergies: z.string().max(500).optional(),
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
      first_name: (me as any).first_name ?? undefined,
      last_name: (me as any).last_name ?? undefined,
      sex: (me as any).sex ?? undefined,
      age: me.age ?? undefined,
      height_cm: me.height_cm ?? undefined,
      weight_kg: me.weight_kg ?? undefined,
      goal: (me.goal ?? undefined) as any,
      activity_level: (me.activity_level ?? undefined) as any,
      training_days_per_week: (me as any).training_days_per_week ?? undefined,
      time_per_session_min: (me as any).time_per_session_min ?? undefined,
      equipment_access: (me as any).equipment_access ?? undefined,
      dietary_preference: (me as any).dietary_preference ?? undefined,
      allergies: (me as any).allergies ?? undefined,
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

  if (isLoading && !me) return <div className="p-4">Cargando...</div>;

  const onSubmit = (data: FormData) => {
    setErrorMsg(null);
    mutation.mutate(data);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-6">
      <PageHeader>
        <h1 className="text-xl font-semibold">Tu perfil</h1>
        <p className="text-sm opacity-90">Completar tu perfil mejora tus planes</p>
      </PageHeader>

      <form onSubmit={handleSubmit(onSubmit)} className="relative grid grid-cols-[180px_minmax(0,1fr)] gap-4">
        <label className="self-center" htmlFor="first_name">Nombre</label>
        <div>
          <input id="first_name" aria-label="Nombre" type="text" className="w-full rounded-2xl shadow border p-2" {...register('first_name')} />
          {errors.first_name && <p className="text-red-500 text-sm">{(errors as any).first_name?.message}</p>}
        </div>

        <label className="self-center" htmlFor="last_name">Apellidos</label>
        <div>
          <input id="last_name" aria-label="Apellidos" type="text" className="w-full rounded-2xl shadow border p-2" {...register('last_name')} />
          {errors.last_name && <p className="text-red-500 text-sm">{(errors as any).last_name?.message}</p>}
        </div>

        <label className="self-center" htmlFor="sex">Sexo</label>
        <div>
          <select id="sex" aria-label="Sexo" className="w-full rounded-2xl shadow border p-2" defaultValue="" {...register('sex')}>
            <option value="" disabled>Selecciona</option>
            <option value="male">Masculino</option>
            <option value="female">Femenino</option>
            <option value="other">Otro / Prefiero no decir</option>
          </select>
        </div>

        <label className="self-center" htmlFor="age">Edad</label>
        <div>
          <input id="age" aria-label="Edad" type="number" className="w-full rounded-2xl shadow border p-2" {...register('age', { valueAsNumber: true })} />
          {errors.age && <p className="text-red-500 text-sm">{errors.age.message}</p>}
        </div>

        <label className="self-center" htmlFor="height_cm">Altura (cm)</label>
        <div>
          <input id="height_cm" aria-label="Altura en centimetros" type="number" className="w-full rounded-2xl shadow border p-2" {...register('height_cm', { valueAsNumber: true })} />
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
            <option value="gain_muscle">Ganar musculo</option>
          </select>
          {errors.goal && <p className="text-red-500 text-sm">{errors.goal.message}</p>}
        </div>

        <label className="self-center" htmlFor="activity_level">Actividad</label>
        <div>
          <select id="activity_level" aria-label="Nivel de actividad" className="w-full rounded-2xl shadow border p-2" defaultValue="" {...register('activity_level')}>
            <option value="" disabled>Selecciona tu actividad</option>
            <option value="sedentary">Sedentario - 0 entrenamientos/semana</option>
            <option value="light">Ligera - 1-2 entrenamientos/semana</option>
            <option value="moderate">Moderada - 3-4 entrenamientos/semana</option>
            <option value="active">Activa - 5-6 entrenamientos/semana</option>
            <option value="very_active">Muy activa - 7+ entrenamientos/semana</option>
          </select>
          <p className="text-xs mt-1 opacity-80">Usamos esto para ajustar tu volumen de entrenamiento y calorias objetivo.</p>
          {errors.activity_level && <p className="text-red-500 text-sm">{errors.activity_level.message}</p>}
        </div>

        <label className="self-center" htmlFor="training_days_per_week">Dias/semana</label>
        <div>
          <input id="training_days_per_week" aria-label="Dias de entrenamiento por semana" type="number" min={0} max={7} className="w-full rounded-2xl shadow border p-2" {...register('training_days_per_week', { valueAsNumber: true })} />
        </div>

        <label className="self-center" htmlFor="time_per_session_min">Tiempo por sesion (min)</label>
        <div>
          <input id="time_per_session_min" aria-label="Tiempo por sesion en minutos" type="number" min={10} max={240} className="w-full rounded-2xl shadow border p-2" {...register('time_per_session_min', { valueAsNumber: true })} />
        </div>

        <label className="self-center" htmlFor="equipment_access">Equipo disponible</label>
        <div>
          <select id="equipment_access" aria-label="Equipo disponible" className="w-full rounded-2xl shadow border p-2" defaultValue="" {...register('equipment_access')}>
            <option value="" disabled>Selecciona equipo</option>
            <option value="none">Sin equipo</option>
            <option value="basic">Basico (mancuernas/bandas)</option>
            <option value="full_gym">Gimnasio completo</option>
          </select>
        </div>

        <label className="self-center" htmlFor="dietary_preference">Preferencia dietetica</label>
        <div>
          <select id="dietary_preference" aria-label="Preferencia dietetica" className="w-full rounded-2xl shadow border p-2" defaultValue="" {...register('dietary_preference')}>
            <option value="" disabled>Selecciona</option>
            <option value="omnivore">Omnivora</option>
            <option value="vegetarian">Vegetariana</option>
            <option value="vegan">Vegana</option>
            <option value="pescatarian">Pescetariana</option>
            <option value="keto">Keto</option>
            <option value="none">Sin preferencia</option>
          </select>
        </div>

        <label className="self-center" htmlFor="allergies">Alergias / intolerancias</label>
        <div>
          <textarea id="allergies" aria-label="Alergias e intolerancias" className="w-full rounded-2xl shadow border p-2 min-h-[80px]" {...register('allergies')} />
        </div>

        <div />
        <div className="flex items-center gap-3">
          <button type="submit" disabled={!isValid || mutation.isPending} className="bg-planifit-500 disabled:opacity-50 text-white px-4 py-2 rounded-2xl shadow">
            {mutation.isPending ? 'Guardando...' : 'Guardar'}
          </button>
          {errorMsg && <span className="text-red-600 text-sm">{errorMsg}</span>}
        </div>
        {mutation.isPending && <Overlay>Guardando tu perfil...</Overlay>}
      </form>
    </div>
  );
}

