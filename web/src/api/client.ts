import { useAuthStore } from '../features/auth/useAuthStore';

const DEMO_MODE = import.meta.env.VITE_DEMO === '1';
const API_URL = DEMO_MODE ? '' : import.meta.env.VITE_API_BASE_URL;

if (DEMO_MODE) {
  console.info('Demo mode active - using mocked API');
}

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

    let refreshData: any = null;
    try {
      refreshData = await refreshRes.json();
    } catch {
      // no se pudo parsear
    }

    if (refreshRes.ok && refreshData?.ok) {
      // Actualizamos el token de acceso usando el valor en refreshData.data.access_token
      setTokens(refreshData.data.access_token, refreshToken);
      // Volvemos a intentar la petición original una sola vez
      return apiFetch<T>(path, options, false);
    }
    // Si no se pudo renovar, cerramos sesión
    logout();
    throw new Error(refreshData?.error?.message || 'Unauthorized');
  }

  // Parseamos el cuerpo de la respuesta (si no es 204)
  let payload: any = null;
  if (res.status !== 204) {
    const text = await res.text();
    try {
      payload = text ? JSON.parse(text) : null;
    } catch {
      payload = text;
    }
  }

  // Si la respuesta no es exitosa, devolvemos el mensaje de error
  if (!res.ok) {
    const message = payload?.error?.message || (typeof payload === 'string' ? payload : res.statusText);
    throw new Error(message);
  }

  // Si no hay contenido (204)
  if (res.status === 204) {
    return undefined as T;
  }

  // Quitamos el envoltorio: si existe la propiedad `ok` y es true, devolvemos payload.data
  if (payload && typeof payload === 'object' && 'ok' in payload) {
    if (payload.ok) {
      return payload.data as T;
    }
    // Si ok es false, lanzamos error con el mensaje
    throw new Error(payload.error?.message || 'Unknown error');
  }

  // Si no hay envoltorio, devolvemos lo recibido
  return payload as T;
}
