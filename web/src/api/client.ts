import { useAuthStore } from '../features/auth/useAuthStore';

const DEMO_MODE = import.meta.env.VITE_DEMO === '1';
const API_URL = DEMO_MODE ? '' : import.meta.env.VITE_API_BASE_URL;

if (DEMO_MODE) {
  console.info('Demo mode active - using mocked API');
}

interface RefreshSuccess {
  ok: true;
  data: { access_token: string };
}
interface RefreshError {
  ok: false;
  error?: { message: string };
}
type RefreshData = RefreshSuccess | RefreshError | null;

export async function apiFetch<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const { accessToken, refreshToken, setTokens, logout } = useAuthStore.getState();
  const headers = new Headers(options.headers);

  // Ponemos tipo JSON por defecto
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  // Añadimos el token de acceso si existe
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  // Hacemos la petición
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  // Si devuelve 401 (token caducado) y tenemos refreshToken, intentamos renovar
  if (res.status === 401 && retry && refreshToken) {
    const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    let refreshData: RefreshData = null;
    try {
      refreshData = await refreshRes.json();
    } catch {
      // no se pudo parsear
    }

    if (refreshRes.ok && refreshData && refreshData.ok) {
      // Actualizamos el token de acceso usando el valor en refreshData.data.access_token
      setTokens(refreshData.data.access_token, refreshToken);
      // Volvemos a intentar la petición original una sola vez
      return apiFetch<T>(path, options, false);
    }
    // Si no se pudo renovar, cerramos sesión
    logout();
    const msg = refreshData && !refreshData.ok ? refreshData.error?.message : 'Unauthorized';
    throw new Error(msg || 'Unauthorized');
  }

  // Parseamos el cuerpo de la respuesta (si no es 204)
  type Payload<U> = { ok: true; data: U } | { ok: false; error?: { message: string } } | U | string | null;
  let payload: Payload<T> = null;
  if (res.status !== 204) {
    const text = await res.text();
    try {
      payload = text ? (JSON.parse(text) as Payload<T>) : null;
    } catch {
      payload = text;
    }
  }

  // Si la respuesta no es exitosa, devolvemos el mensaje de error
  if (!res.ok) {
    const message =
      typeof payload === 'object' && payload && 'error' in payload
        ? payload.error?.message || res.statusText
        : typeof payload === 'string'
        ? payload
        : res.statusText;
    throw new Error(message);
  }

  // Si no hay contenido (204)
  if (res.status === 204) {
    return undefined as T;
  }

  // Quitamos el envoltorio: si existe la propiedad `ok` y es true, devolvemos payload.data
  if (payload && typeof payload === 'object' && 'ok' in payload) {
    const data = payload as { ok: boolean; data: T; error?: { message: string } };
    if (data.ok) {
      return data.data;
    }
    // Si ok es false, lanzamos error con el mensaje
    throw new Error(data.error?.message || 'Unknown error');
  }

  // Si no hay envoltorio, devolvemos lo recibido
  return payload as T;
}
