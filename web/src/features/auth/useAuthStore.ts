import { create } from 'zustand';
import type { User } from '../../api/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: localStorage.getItem('refresh_token'),
  setTokens: (access, refresh) => {
    set({ accessToken: access, refreshToken: refresh });
    localStorage.setItem('refresh_token', refresh);
  },
  setUser: (user) => set({ user }),
  logout: () => {
    set({ user: null, accessToken: null, refreshToken: null });
    localStorage.removeItem('refresh_token');
  },
}));
