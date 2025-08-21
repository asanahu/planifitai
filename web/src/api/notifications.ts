import { apiFetch } from './client';

export interface Notification {
  id: string;
  message: string;
  state: string;
}

export function listNotifications(params: { state?: string } = {}) {
  const search = new URLSearchParams(params as Record<string, string>);
  const query = search.toString();
  return apiFetch<Notification[]>(`/notifications${query ? `?${query}` : ''}`);
}

export function readNotification(id: string) {
  return apiFetch(`/notifications/${id}/read`, { method: 'PATCH' });
}
