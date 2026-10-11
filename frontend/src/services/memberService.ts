/**
 * KEEP Enterprise Platform — Organization Member API Client Service.
 * Connects frontend UI components to backend member management endpoints (/api/v1/members).
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  MemberResponse,
  MemberUpdate,
  MemberListQuery,
} from '@/types/member';

export const memberService = {
  /**
   * List enterprise members with pagination and filtering.
   * GET /api/v1/members
   */
  async listMembers(
    params?: MemberListQuery
  ): Promise<ApiResponse<PaginatedData<MemberResponse>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<MemberResponse>>>(
      '/members',
      { params }
    );
    return response.data;
  },

  /**
   * Update member role, department, team assignment, or active status.
   * PATCH /api/v1/members/{user_id}
   */
  async updateMember(
    userId: string,
    data: MemberUpdate
  ): Promise<ApiResponse<MemberResponse>> {
    const response = await apiClient.patch<ApiResponse<MemberResponse>>(
      `/members/${userId}`,
      data
    );
    return response.data;
  },

  /**
   * Remove member from organization.
   * DELETE /api/v1/members/{user_id}
   */
  async removeMember(
    userId: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(
      `/members/${userId}`
    );
    return response.data;
  },
};

export default memberService;
