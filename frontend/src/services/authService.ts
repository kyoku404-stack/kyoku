/**
 * KEEP Enterprise Platform — Authentication Service Client.
 * Connects to /api/v1/auth endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  LoginRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  TokenResponse,
  UserProfileResponse,
} from '@/types/auth';

export const authService = {
  /**
   * Authenticate corporate credentials and issue JWT tokens.
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
  async logout(): Promise<ApiResponse<{ user_id: string }>> {
    const response = await apiClient.post<ApiResponse<{ user_id: string }>>('/auth/logout');
    return response.data;
  },
};

export default authService;
