import { apiFetch } from './client';

export type NotificationCategory = 'routine' | 'nutrition' | 'progress' | 'system';
export type NotificationType =
  | 'workout_reminder'
  | 'meal_reminder'
  | 'water_reminder'
  | 'weigh_in'
  | 'progress_daily'
  | 'progress_weekly'
  | 'custom';
export type NotificationStatus = 'scheduled' | 'sent' | 'failed' | 'cancelled';

export interface Notification {
  id: number;
  category: NotificationCategory;
  type: NotificationType;
  title: string;
  body: string;
  payload?: Record<string, unknown> | null;
  scheduled_at_utc: string;
  sent_at_utc?: string | null;
  read_at_utc?: string | null;
  dismissed_at_utc?: string | null;
  status: NotificationStatus;
  delivered_channels?: string[] | null;
}

export function listNotifications(params: { status?: string; limit?: number; offset?: number; auto?: boolean } = {}) {
  const search = new URLSearchParams();
  if (params.status) search.set('status', params.status);
  if (params.limit != null) search.set('limit', String(params.limit));
  if (params.offset != null) search.set('offset', String(params.offset));
  if (params.auto != null) search.set('auto', params.auto ? '1' : '0');
  const query = search.toString();
  return apiFetch<Notification[]>(`/notifications${query ? `?${query}` : ''}`);
}

export function markAsRead(id: number) {
  return apiFetch<Notification>(`/notifications/${id}/read`, { method: 'PATCH' });
}
