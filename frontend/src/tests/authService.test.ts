import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '@/services/api';
import { authService } from '@/services/authService';
import type { ApiResponse } from '@/types/api';
import type {
  TokenResponse,
  UserProfileResponse,
  ForgotPasswordResponse,
  ResetPasswordResponse,
  ChangePasswordResponse,
  LogoutResponse,
} from '@/types/auth';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: 'http://localhost:8000/api/v1' },
    },
  };
});

describe('Phase 1.4 authService API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('register calls POST /auth/register', async () => {
    const mockResponse: ApiResponse<UserProfileResponse> = {
      success: true,
      message: 'Registered.',
      data: {
        id: 'u1',
        email: 'test@enterprise.com',
        full_name: 'Test User',
        role: 'Member',
        organization_id: 'org1',
        is_active: true,
        created_at: '2026-10-09T00:00:00Z',
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

    const res = await authService.register({
      email: 'test@enterprise.com',
      password: 'Password123!',
      full_name: 'Test User',
      organization_id: 'org1',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/register', {
      email: 'test@enterprise.com',
      password: 'Password123!',
      full_name: 'Test User',
      organization_id: 'org1',
    });
    expect(res.data.id).toBe('u1');
  });

  it('login calls POST /auth/login', async () => {
    const mockResponse: ApiResponse<TokenResponse> = {
      success: true,
      message: 'Logged in.',
      data: {
        access_token: 'acc_token',
        refresh_token: 'ref_token',
        token_type: 'bearer',
        expires_in: 1800,
        user: {
          id: 'u1',
          email: 'test@enterprise.com',
          full_name: 'Test User',
          role: 'OrgAdmin',
          organization_id: 'org1',
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

    const res = await authService.login({
      email: 'test@enterprise.com',
      password: 'Password123!',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
      email: 'test@enterprise.com',
      password: 'Password123!',
    });
    expect(res.data.access_token).toBe('acc_token');
  });

  it('forgotPassword calls POST /auth/forgot-password', async () => {
    const mockResponse: ApiResponse<ForgotPasswordResponse> = {
      success: true,
      message: 'Email sent.',
      data: { email_sent: true },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

    const res = await authService.forgotPassword({ email: 'test@enterprise.com' });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/forgot-password', {
      email: 'test@enterprise.com',
    });
    expect(res.data.email_sent).toBe(true);
  });

  it('resetPassword calls POST /auth/reset-password', async () => {
    const mockResponse: ApiResponse<ResetPasswordResponse> = {
      success: true,
      message: 'Reset complete.',
      data: { reset_completed: true },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

    const res = await authService.resetPassword({
      token: 'reset_tok',
      new_password: 'NewPassword123!',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/reset-password', {
      token: 'reset_tok',
      new_password: 'NewPassword123!',
    });
    expect(res.data.reset_completed).toBe(true);
  });

  it('changePassword calls PATCH /auth/change-password', async () => {
    const mockResponse: ApiResponse<ChangePasswordResponse> = {
      success: true,
      message: 'Password changed.',
      data: { password_changed: true },
    };

    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockResponse });

    const res = await authService.changePassword({
      current_password: 'OldPassword123!',
      new_password: 'NewPassword123!',
    });

    expect(apiClient.patch).toHaveBeenCalledWith('/auth/change-password', {
      current_password: 'OldPassword123!',
      new_password: 'NewPassword123!',
    });
    expect(res.data.password_changed).toBe(true);
  });

  it('logout calls POST /auth/logout with optional refresh token payload', async () => {
    const mockResponse: ApiResponse<LogoutResponse> = {
      success: true,
      message: 'Logged out.',
      data: { logged_out: true },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

    const res = await authService.logout('refresh_tok');

    expect(apiClient.post).toHaveBeenCalledWith('/auth/logout', {
      refresh_token: 'refresh_tok',
    });
    expect(res.data.logged_out).toBe(true);
  });
});
