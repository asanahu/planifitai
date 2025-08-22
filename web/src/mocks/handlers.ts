import { http, HttpResponse } from 'msw';

const read = <T>(key: string, fallback: T): T => {
  const raw = localStorage.getItem(key);
  return raw ? (JSON.parse(raw) as T) : fallback;
};

const write = (key: string, value: unknown) => {
  localStorage.setItem(key, JSON.stringify(value));
};

export const seedDemoData = () => {
  if (!localStorage.getItem('demo:user')) {
    write('demo:user', { id: 1, email: 'demo@demo.com' });
  }
  if (!localStorage.getItem('demo:routines')) {
    write('demo:routines', []);
  }
  if (!localStorage.getItem('demo:nutrition')) {
    write('demo:nutrition', { days: [], summary: [] });
  }
  if (!localStorage.getItem('demo:progress')) {
    write('demo:progress', []);
  }
  if (!localStorage.getItem('demo:profile')) {
    write('demo:profile', null);
  }
  if (!localStorage.getItem('demo:notifications')) {
    write('demo:notifications', []);
  }
};

export const handlers = [
  http.post('/auth/register', async ({ request }) => {
    const body = (await request.json()) as { email: string };
    write('demo:user', { id: 1, email: body.email });
    return HttpResponse.json({ access_token: 'demo', refresh_token: 'demo' });
  }),
  http.post('/auth/login', async ({ request }) => {
    const body = (await request.json()) as { email: string };
    write('demo:user', { id: 1, email: body.email });
    return HttpResponse.json({ access_token: 'demo', refresh_token: 'demo' });
  }),
  http.post('/auth/refresh', () =>
    HttpResponse.json({ access_token: 'demo', refresh_token: 'demo' })
  ),
  http.get('/auth/me', () => {
    const user = read('demo:user', null);
    return HttpResponse.json(user);
  }),

  http.get('/profiles', () => {
    const profile = read('demo:profile', null);
    return HttpResponse.json(profile);
  }),
  http.post('/profiles', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const profile = { id: 1, ...body };
    write('demo:profile', profile);
    return HttpResponse.json(profile);
  }),

  http.get('/routines', () => {
    const routines = read('demo:routines', []);
    return HttpResponse.json(routines);
  }),
  http.post('/routines', async ({ request }) => {
    const routines = read('demo:routines', [] as unknown[]);
    const body = await request.json();
    routines.push(body as unknown);
    write('demo:routines', routines);
    return HttpResponse.json(body);
  }),

  http.get('/nutrition', () => {
    const data = read('demo:nutrition', { days: [], summary: [] });
    return HttpResponse.json(data);
  }),
  http.post('/nutrition', async ({ request }) => {
    const data = read('demo:nutrition', { days: [] as Record<string, unknown>[], summary: [] });
    const body = await request.json();
    data.days.push(body as Record<string, unknown>);
    write('demo:nutrition', data);
    return HttpResponse.json(body);
  }),

  http.get('/progress', () => {
    const data = read('demo:progress', []);
    return HttpResponse.json(data);
  }),
  http.post('/progress', async ({ request }) => {
    const data = read('demo:progress', [] as unknown[]);
    const body = await request.json();
    data.push(body as unknown);
    write('demo:progress', data);
    return HttpResponse.json(body);
  }),

  http.get('/notifications', () => {
    const data = read('demo:notifications', []);
    return HttpResponse.json(data);
  }),
  http.patch('/notifications/:id', async ({ params }) => {
    const data = read('demo:notifications', [] as { id: string; read?: boolean }[]);
    const idx = data.findIndex((n) => n.id === params.id);
    if (idx >= 0) data[idx].read = true;
    write('demo:notifications', data);
    return HttpResponse.json(data[idx]);
  }),
];

export const resetDemoData = () => {
  Object.keys(localStorage)
    .filter((k) => k.startsWith('demo:'))
    .forEach((k) => localStorage.removeItem(k));
};
