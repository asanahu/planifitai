import type { Profile } from "../../api/profile";
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { createProfile, updateProfile } from '../../api/profile';

const schema = z.object({
  age: z.number().int().min(1),
  weight: z.number().min(1),
  height: z.number().min(1),
  goal: z.string().min(1),
  activity: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

export function ProfileForm({ profile }: { profile?: Profile }) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: profile ?? { age: 0, weight: 0, height: 0, goal: '', activity: '' },
  });

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
      <input placeholder="Goal" {...register('goal')} className="w-full border p-2" />
      <input placeholder="Activity" {...register('activity')} className="w-full border p-2" />
      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">Save</button>
    </form>
  );
}
