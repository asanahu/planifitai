import { apiFetch } from './client';

export interface ProgressEntry {
  id: string;
  metric: string;
  value: number;
  date: string;
}

export function addEntry(data: { metric: string; value: number; date: string }) {
  return apiFetch('/progress', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getEntries(metric: string, start: string, end: string) {
  return apiFetch<ProgressEntry[]>(`/progress?metric=${metric}&start=${start}&end=${end}`);
}
