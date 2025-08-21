import type { ReactNode } from "react";
import { useEffect } from 'react';
import { useAuthStore } from '../features/auth/useAuthStore';
import { me } from '../api/auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const { accessToken, refreshToken, setTokens, setUser } = useAuthStore();

  useEffect(() => {
    const init = async () => {
      if (!accessToken && refreshToken) {
        try {
          const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (res.ok) {
            const data = await res.json();
            setTokens(data.access_token, refreshToken);
          }
        } catch {
          /* ignore */
        }
      }
      if (accessToken) {
        try {
          const user = await me();
          setUser(user);
        } catch {
          /* ignore */
        }
      }
    };
    init();
  }, [accessToken, refreshToken, setTokens, setUser]);

  return <>{children}</>;
}
