import { create } from 'zustand';
import type { UserProfileResponse, UserRole } from '@/types/auth';
import { authService } from '@/services/authService';

interface AuthState {
  user: UserProfileResponse | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setAuth: (
    user: UserProfileResponse,
    token: string,
    refreshToken?: string | null
  ) => void;
  setUser: (user: UserProfileResponse) => void;
  clearAuth: () => void;
  hasRole: (allowedRoles: UserRole[]) => boolean;
  initializeSession: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('keep_auth_token'),
  refreshToken: localStorage.getItem('keep_refresh_token'),
  isAuthenticated: !!localStorage.getItem('keep_auth_token'),
  isLoading: false,

  setAuth: (user, token, refreshToken) => {
    localStorage.setItem('keep_auth_token', token);
    if (refreshToken) {
      localStorage.setItem('keep_refresh_token', refreshToken);
    }
    set({
      user,
      token,
      refreshToken: refreshToken || get().refreshToken,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  setUser: (user) => {
    set({ user });
  },

  clearAuth: () => {
    localStorage.removeItem('keep_auth_token');
    localStorage.removeItem('keep_refresh_token');
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  hasRole: (allowedRoles) => {
    const user = get().user;
    if (!user) return false;
    return allowedRoles.includes(user.role);
  },

  initializeSession: async () => {
    const token = localStorage.getItem('keep_auth_token');
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }

    set({ isLoading: true });
    try {
      const response = await authService.getCurrentUser();
      if (response.success && response.data) {
        set({
          user: response.data,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        get().clearAuth();
      }
    } catch {
      // If fetching profile fails, clear stored invalid token
      get().clearAuth();
    }
  },

  logout: async () => {
    const refresh = get().refreshToken;
    try {
      if (get().isAuthenticated) {
        await authService.logout(refresh || undefined);
      }
    } catch {
      // Ignore network errors during logout
    } finally {
      get().clearAuth();
    }
  },
}));
