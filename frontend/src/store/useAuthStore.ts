import { create } from 'zustand';
import type { User } from '@/types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('keep_auth_token'),
  isAuthenticated: !!localStorage.getItem('keep_auth_token'),

  setAuth: (user, token) => {
    localStorage.setItem('keep_auth_token', token);
    set({ user, token, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem('keep_auth_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
