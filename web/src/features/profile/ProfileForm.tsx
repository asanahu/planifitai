import type { Profile } from "../../api/profile";
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { createProfile, updateProfile } from '../../api/profile';
import { useState, useId } from 'react';

const schema = z.object({
  age: z.number().int().min(1),
  weight: z.number().min(1),
  height: z.number().min(1),
  goal: z.string().min(1),
  activity: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

const goalOptions = [
  { value: 'perder_peso', label: 'Perder peso', info: 'Reduce peso con un plan equilibrado.' },
  { value: 'ganar_musculo', label: 'Ganar músculo', info: 'Incrementa tu fuerza y masa muscular.' },
  { value: 'mantener', label: 'Mantenerme', info: 'Mantén tu forma actual.' },
];

const activityOptions = [
  { value: 'sedentaria', label: 'Sedentaria', info: 'Poco o ningún ejercicio.' },
  { value: 'ligera', label: 'Ligera', info: 'Ejercicio 1-3 días por semana.' },
  { value: 'moderada', label: 'Moderada', info: 'Ejercicio moderado 3-5 días.' },
  { value: 'intensa', label: 'Intensa', info: 'Entrenamiento duro 6-7 días.' },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className="border rounded">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={id}
        className="flex w-full justify-between p-2 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      >
        <span>{title}</span>
        <span>{open ? '-' : '+'}</span>
      </button>
      <div id={id} hidden={!open} className="p-2">
        {children}
      </div>
    </div>
  );
}

export function ProfileForm({ profile }: { profile?: Profile }) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: profile ?? { age: 0, weight: 0, height: 0, goal: '', activity: '' },
  });
  const goal = watch('goal');
  const activity = watch('activity');

  const onSubmit = async (data: FormData) => {
    if (profile) {
      await updateProfile(profile.id, data);
    } else {
      await createProfile(data);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-2 max-w-md">
      <input type="number" placeholder="Age" {...register('age', { valueAsNumber: true })} className="w-full border p-2" />
      {errors.age && <p className="text-red-500 text-sm">{errors.age.message}</p>}
      <input type="number" placeholder="Weight" {...register('weight', { valueAsNumber: true })} className="w-full border p-2" />
      <input type="number" placeholder="Height" {...register('height', { valueAsNumber: true })} className="w-full border p-2" />
      <Section title="Objetivo">
        <label htmlFor="goal" className="block text-sm">Objetivo</label>
        <select
          id="goal"
          {...register('goal')}
          className="w-full border p-2 mt-1"
        >
          <option value="">Selecciona…</option>
          {goalOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {errors.goal && <p className="text-red-500 text-sm">{errors.goal.message}</p>}
        {goal && (
          <p className="mt-2 text-sm" role="note">
            {goalOptions.find((o) => o.value === goal)?.info}
          </p>
        )}
      </Section>
      <Section title="Actividad">
        <label htmlFor="activity" className="block text-sm">Actividad</label>
        <select
          id="activity"
          {...register('activity')}
          className="w-full border p-2 mt-1"
        >
          <option value="">Selecciona…</option>
          {activityOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {errors.activity && <p className="text-red-500 text-sm">{errors.activity.message}</p>}
        {activity && (
          <p className="mt-2 text-sm" role="note">
            {activityOptions.find((o) => o.value === activity)?.info}
          </p>
        )}
      </Section>
      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">Save</button>
    </form>
  );
}
