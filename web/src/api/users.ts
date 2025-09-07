import { apiFetch } from './client';

export interface MeResponse {
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  goal: 'lose_weight' | 'maintain' | 'gain_muscle' | null;
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null;
  profile_completed: boolean;
}

export interface ProfileIn {
  age: number;
  height_cm: number;
  weight_kg: number;
  goal: 'lose_weight' | 'maintain' | 'gain_muscle';
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
}

export function getMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>('/users/me');
}

export function updateMyProfile(payload: ProfileIn): Promise<MeResponse> {
  return apiFetch<MeResponse>('/users/me/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}


