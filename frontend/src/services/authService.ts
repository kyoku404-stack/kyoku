/**
 * KEEP Enterprise Platform — Authentication Service Client.
 * Connects frontend components to /api/v1/auth endpoints (devdocs/p1/p1.4.txt Chapter 19).
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  LoginRequest,
  RegisterRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  TokenResponse,
  UserProfileResponse,
  ForgotPasswordRequest,
  ForgotPasswordResponse,
  ResetPasswordRequest,
  ResetPasswordResponse,
  ChangePasswordRequest,
  ChangePasswordResponse,
  LogoutResponse,
} from '@/types/auth';

export const authService = {
  /**
   * Register a new user account.
   * POST /api/v1/auth/register
   */
  async register(data: RegisterRequest): Promise<ApiResponse<UserProfileResponse>> {
    const response = await apiClient.post<ApiResponse<UserProfileResponse>>(
      '/auth/register',
      data
    );
    return response.data;
  },

  /**
   * Authenticate corporate credentials and issue JWT access and refresh tokens.
   * POST /api/v1/auth/login
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<TokenResponse>> {
    const response = await apiClient.post<ApiResponse<TokenResponse>>(
      '/auth/login',
      credentials
    );
    return response.data;
  },

  /**
   * Refreshes an expired access token using a valid refresh token.
   * POST /api/v1/auth/refresh
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<RefreshTokenResponse>> {
    const payload: RefreshTokenRequest = { refresh_token: refreshToken };
    const response = await apiClient.post<ApiResponse<RefreshTokenResponse>>(
      '/auth/refresh',
      payload
    );
    return response.data;
  },

  /**
   * Request password reset instructions via email.
   * POST /api/v1/auth/forgot-password
   */
  async forgotPassword(
    data: ForgotPasswordRequest
  ): Promise<ApiResponse<ForgotPasswordResponse>> {
    const response = await apiClient.post<ApiResponse<ForgotPasswordResponse>>(
      '/auth/forgot-password',
      data
    );
    return response.data;
  },

  /**
   * Reset password using verification token.
   * POST /api/v1/auth/reset-password
   */
  async resetPassword(
    data: ResetPasswordRequest
  ): Promise<ApiResponse<ResetPasswordResponse>> {
    const response = await apiClient.post<ApiResponse<ResetPasswordResponse>>(
      '/auth/reset-password',
      data
    );
    return response.data;
  },

  /**
   * Update password for currently authenticated user.
   * PATCH /api/v1/auth/change-password
   */
  async changePassword(
    data: ChangePasswordRequest
  ): Promise<ApiResponse<ChangePasswordResponse>> {
    const response = await apiClient.patch<ApiResponse<ChangePasswordResponse>>(
      '/auth/change-password',
      data
    );
    return response.data;
  },

  /**
   * Fetches profile data of the currently authenticated user.
   * GET /api/v1/auth/me
   */
  async getCurrentUser(): Promise<ApiResponse<UserProfileResponse>> {
    const response = await apiClient.get<ApiResponse<UserProfileResponse>>('/auth/me');
    return response.data;
  },

  /**
   * Terminates active session and invalidates client credentials.
   * POST /api/v1/auth/logout
   */
  async logout(refreshToken?: string): Promise<ApiResponse<LogoutResponse>> {
    const payload = refreshToken ? { refresh_token: refreshToken } : {};
    const response = await apiClient.post<ApiResponse<LogoutResponse>>(
      '/auth/logout',
      payload
    );
    return response.data;
  },
};

export default authService;
