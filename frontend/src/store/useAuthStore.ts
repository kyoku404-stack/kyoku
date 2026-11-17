import { create } from 'zustand';
import type { UserProfileResponse, UserRole } from '@/types/auth';
import {
  ROLE_HIERARCHY,
  ROLE_PERMISSIONS_MAP,
} from '@/types/permission';
import { authService } from '@/services/authService';

interface AuthState {
  user: UserProfileResponse | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  simulatedRole: UserRole | null;

  setAuth: (
    user: UserProfileResponse,
    token: string,
    refreshToken?: string | null
  ) => void;
  setUser: (user: UserProfileResponse) => void;
  clearAuth: () => void;
  setSimulatedRole: (role: UserRole | null) => void;
  getEffectiveRole: () => UserRole;
  hasRole: (allowedRoles: UserRole[]) => boolean;
  isAtLeastRole: (minRole: UserRole) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  getPermissions: () => Set<string>;
  initializeSession: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user:
    typeof window !== 'undefined' &&
    (window as unknown as { __MOCK_USER__?: UserProfileResponse }).__MOCK_USER__
      ? (window as unknown as { __MOCK_USER__: UserProfileResponse }).__MOCK_USER__
      : (() => {
          try {
            const stored = typeof window !== 'undefined' ? localStorage.getItem('keep_user') : null;
            return stored ? JSON.parse(stored) : null;
          } catch {
            return null;
          }
        })(),
  token: typeof window !== 'undefined' ? localStorage.getItem('keep_auth_token') : null,
  refreshToken: typeof window !== 'undefined' ? localStorage.getItem('keep_refresh_token') : null,
  isAuthenticated:
    typeof window !== 'undefined'
      ? !!localStorage.getItem('keep_auth_token') ||
        !!(window as unknown as { __MOCK_USER__?: UserProfileResponse }).__MOCK_USER__
      : false,
  isLoading: false,
  simulatedRole: null,

  setAuth: (user, token, refreshToken) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('keep_auth_token', token);
      localStorage.setItem('keep_user', JSON.stringify(user));
      if (refreshToken) {
        localStorage.setItem('keep_refresh_token', refreshToken);
      }
    }
    set({
      user,
      token,
      refreshToken: refreshToken || get().refreshToken,
      isAuthenticated: true,
      isLoading: false,
      simulatedRole: null,
    });
  },

  setUser: (user) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('keep_user', JSON.stringify(user));
    }
    set({ user });
  },

  clearAuth: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('keep_auth_token');
      localStorage.removeItem('keep_refresh_token');
      localStorage.removeItem('keep_user');
      delete (window as unknown as { __MOCK_USER__?: UserProfileResponse }).__MOCK_USER__;
    }
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      simulatedRole: null,
    });
  },

  setSimulatedRole: (role) => {
    set({ simulatedRole: role });
  },

  getEffectiveRole: (): UserRole => {
    const { simulatedRole, user } = get();
    if (simulatedRole) return simulatedRole;
    if (user?.role) return user.role;
    return 'Guest';
  },

  hasRole: (allowedRoles) => {
    const effectiveRole = get().getEffectiveRole();
    return allowedRoles.includes(effectiveRole);
  },

  isAtLeastRole: (minRole) => {
    const effectiveRole = get().getEffectiveRole();
    const currentLevel = ROLE_HIERARCHY[effectiveRole] ?? 0;
    const requiredLevel = ROLE_HIERARCHY[minRole] ?? 0;
    return currentLevel >= requiredLevel;
  },

  getPermissions: (): Set<string> => {
    const effectiveRole = get().getEffectiveRole();
    return ROLE_PERMISSIONS_MAP[effectiveRole] ?? new Set();
  },

  hasPermission: (permission) => {
    const permissions = get().getPermissions();
    return permissions.has(permission);
  },

  hasAllPermissions: (permissions) => {
    const userPerms = get().getPermissions();
    return permissions.every((p) => userPerms.has(p));
  },

  hasAnyPermission: (permissions) => {
    const userPerms = get().getPermissions();
    return permissions.some((p) => userPerms.has(p));
  },

  initializeSession: async () => {
    if (
      typeof window !== 'undefined' &&
      (window as unknown as { __MOCK_USER__?: UserProfileResponse }).__MOCK_USER__
    ) {
      set({
        user: (window as unknown as { __MOCK_USER__: UserProfileResponse }).__MOCK_USER__,
        isAuthenticated: true,
        isLoading: false,
      });
      return;
    }
    const token = typeof window !== 'undefined' ? localStorage.getItem('keep_auth_token') : null;
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }

    set({ isLoading: true });
    try {
      const response = await authService.getCurrentUser();
      if (response.success && response.data) {
        if (typeof window !== 'undefined') {
          localStorage.setItem('keep_user', JSON.stringify(response.data));
        }
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
