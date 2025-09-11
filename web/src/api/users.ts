import { apiFetch } from './client';

export interface MeResponse {
  first_name?: string | null;
  last_name?: string | null;
  sex?: 'male' | 'female' | 'other' | null;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  goal: 'lose_weight' | 'maintain' | 'gain_muscle' | null;
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active' | null;
  training_days_per_week?: number | null;
  time_per_session_min?: number | null;
  equipment_access?: 'none' | 'basic' | 'full_gym' | null;
  dietary_preference?: 'omnivore' | 'vegetarian' | 'vegan' | 'pescatarian' | 'keto' | 'none' | null;
  allergies?: string | null;
  profile_completed: boolean;
}

export interface ProfileIn {
  first_name?: string;
  last_name?: string;
  sex?: 'male' | 'female' | 'other';
  age: number;
  height_cm: number;
  weight_kg: number;
  goal: 'lose_weight' | 'maintain' | 'gain_muscle';
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
  training_days_per_week?: number;
  time_per_session_min?: number;
  equipment_access?: 'none' | 'basic' | 'full_gym';
  dietary_preference?: 'omnivore' | 'vegetarian' | 'vegan' | 'pescatarian' | 'keto' | 'none';
  allergies?: string;
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


