import { apiFetch } from './client';

export interface ProgressEntry {
  id: string;
  metric: string;
  value: number;
  date: string;
}

export function createProgressEntry(data: { metric: string; value: number; date: string; unit?: string }) {
  return apiFetch('/progress', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function listProgress({ metric, start, end }: { metric: string; start: string; end: string }) {
  return apiFetch<ProgressEntry[]>(`/progress?metric=${metric}&start=${start}&end=${end}`);
}

export function summaryProgress({ metric, start, end }: { metric: string; start: string; end: string }) {
  return apiFetch<{ date: string; value: number }[]>(`/progress/summary?metric=${metric}&start=${start}&end=${end}`);
}

// backward compatible exports
export const addEntry = createProgressEntry;
export const getEntries = (metric: string, start: string, end: string) =>
  listProgress({ metric, start, end });
export const getSummary = (metric: string, start: string, end: string) =>
  summaryProgress({ metric, start, end });
