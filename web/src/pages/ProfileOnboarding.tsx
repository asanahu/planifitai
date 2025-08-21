import type { Profile } from "../api/profile";
import { useQuery } from '@tanstack/react-query';
import { getProfile } from '../api/profile';
import { ProfileForm } from '../features/profile/ProfileForm';

export default function ProfileOnboardingPage() {
  const { data } = useQuery<Profile | null>({ queryKey: ['profile'], queryFn: getProfile });
  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Perfil</h1>
      <ProfileForm profile={data || undefined} />
    </div>
  );
}
