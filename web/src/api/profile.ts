import { apiFetch } from './client';

export interface Profile {
  id: string;
  age: number;
  weight: number;
  height: number;
  goal: string;
  activity: string;
}

export function getProfile() {
  return apiFetch<Profile | null>('/profiles/');
}

export function createProfile(data: Omit<Profile, 'id'>) {
  return apiFetch<Profile>('/profiles/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateProfile(id: string, data: Omit<Profile, 'id'>) {
  return apiFetch<Profile>(`/profiles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
