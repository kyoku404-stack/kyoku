/**
 * KEEP Enterprise Platform — User Invitation API Client Service.
 * Connects frontend UI components to backend invitation management endpoints (/api/v1/invitations).
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  InvitationResponse,
  InvitationCreate,
  InvitationAccept,
} from '@/types/invitation';

export const invitationService = {
  /**
   * List pending/active invitations for the tenant organization.
   * GET /api/v1/invitations
   */
  async listInvitations(
    skip = 0,
    limit = 100
  ): Promise<ApiResponse<InvitationResponse[]>> {
    const response = await apiClient.get<ApiResponse<InvitationResponse[]>>(
      '/invitations',
      { params: { skip, limit } }
    );
    return response.data;
  },

  /**
   * Dispatch a new user invitation.
   * POST /api/v1/invitations
   */
  async createInvitation(
    data: InvitationCreate
  ): Promise<ApiResponse<InvitationResponse>> {
    const response = await apiClient.post<ApiResponse<InvitationResponse>>(
      '/invitations',
      data
    );
    return response.data;
  },

  /**
   * Revoke/cancel a pending invitation.
   * DELETE /api/v1/invitations/{id}
   */
  async revokeInvitation(
    id: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(
      `/invitations/${id}`
    );
    return response.data;
  },

  /**
   * Accept an invitation token and initialize user account credentials.
   * POST /api/v1/invitations/accept
   */
  async acceptInvitation(
    data: InvitationAccept
  ): Promise<ApiResponse<{ user_id: string; email: string; organization_id: string }>> {
    const response = await apiClient.post<
      ApiResponse<{ user_id: string; email: string; organization_id: string }>
    >('/invitations/accept', data);
    return response.data;
  },
};

export default invitationService;
