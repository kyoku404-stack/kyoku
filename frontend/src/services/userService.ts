/**
 * KEEP Enterprise Platform — User Management Service Client.
 * Connects to /api/v1/users endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type { UserProfileResponse } from '@/types/auth';
import type { UserFilterParams } from '@/types/user';

export const userService = {
  /**
   * Retrieves paginated users for the tenant organization.
   * GET /api/v1/users
   */
  async listUsers(
    params?: UserFilterParams
  ): Promise<ApiResponse<PaginatedData<UserProfileResponse>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<UserProfileResponse>>>(
      '/users',
      { params }
    );
    return response.data;
  },

  /**
   * Retrieves specific user details by ID.
   * GET /api/v1/users/{user_id}
   */
  async getUserById(userId: string): Promise<ApiResponse<UserProfileResponse>> {
    const response = await apiClient.get<ApiResponse<UserProfileResponse>>(
      `/users/${userId}`
    );
    return response.data;
  },
};

export default userService;
