import { apiFetch } from './client';

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

export interface User {
  id: string;
  email: string;
}

export async function register(data: { email: string; password: string }): Promise<AuthResponse & { user: User }> {
  return apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function login(data: { username: string; password: string }): Promise<AuthResponse> {
  const body = new URLSearchParams();
  body.set('username', data.username);
  body.set('password', data.password);
  return apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });
}

export async function me(): Promise<User> {
  return apiFetch('/auth/me');
}
