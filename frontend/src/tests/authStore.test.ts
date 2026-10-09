import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/useAuthStore';
import { authService } from '@/services/authService';
import type { UserProfileResponse } from '@/types/auth';

vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}));

describe('Phase 1.4 useAuthStore Session Management', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().clearAuth();
    vi.clearAllMocks();
  });

  const mockUser: UserProfileResponse = {
    id: 'u1',
    email: 'jane@enterprise.com',
    full_name: 'Jane Doe',
    role: 'OrgAdmin',
    organization_id: 'org1',
    is_active: true,
    created_at: '2026-10-09T00:00:00Z',
  };

  it('sets authentication state and persists tokens to localStorage', () => {
    useAuthStore.getState().setAuth(mockUser, 'access_123', 'refresh_456');

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe('access_123');
    expect(state.refreshToken).toBe('refresh_456');
    expect(localStorage.getItem('keep_auth_token')).toBe('access_123');
    expect(localStorage.getItem('keep_refresh_token')).toBe('refresh_456');
  });

  it('clears authentication state and removes tokens from localStorage', () => {
    useAuthStore.getState().setAuth(mockUser, 'access_123', 'refresh_456');
    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(localStorage.getItem('keep_auth_token')).toBeNull();
  });

  it('checks role permissions correctly via hasRole', () => {
    useAuthStore.getState().setAuth(mockUser, 'acc_token');
    const state = useAuthStore.getState();

    expect(state.hasRole(['OrgAdmin', 'SuperAdmin'])).toBe(true);
    expect(state.hasRole(['Viewer'])).toBe(false);
  });

  it('initializeSession fetches profile if token exists', async () => {
    localStorage.setItem('keep_auth_token', 'valid_token');

    vi.mocked(authService.getCurrentUser).mockResolvedValueOnce({
      success: true,
      message: 'Profile',
      data: mockUser,
    });

    await useAuthStore.getState().initializeSession();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
  });
});
