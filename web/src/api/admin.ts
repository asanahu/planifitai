import { apiFetch } from './client';

export function importWger(language = 'es', dry_run = false) {
  const headers: Record<string, string> = {};
  const secret = import.meta.env.VITE_ADMIN_SECRET;
  if (secret) headers['X-Admin-Secret'] = secret as string;
  return apiFetch<{ imported: number }>(
    '/admin/exercises/import/wger',
    { method: 'POST', headers, body: JSON.stringify({ language, dry_run }) }
  );
}

export function importFreeDB(url?: string, path?: string, dry_run = false) {
  const headers: Record<string, string> = {};
  const secret = import.meta.env.VITE_ADMIN_SECRET;
  if (secret) headers['X-Admin-Secret'] = secret as string;
  const body = JSON.stringify({ url, path, dry_run });
  return apiFetch<{ imported: number }>(
    '/admin/exercises/import/free-db',
    { method: 'POST', headers, body }
  );
}

