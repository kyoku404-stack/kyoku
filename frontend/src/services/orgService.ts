/**
 * KEEP Enterprise Platform — Organization & Tenant Service Client.
 * Connects to /api/v1/organizations endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  OrganizationResponse,
  OrganizationCreate,
  OrganizationUpdate,
} from '@/types/organization';

export const orgService = {
  /**
   * Retrieves active tenant organization details.
   * GET /api/v1/organizations/current
   */
  async getCurrentOrganization(): Promise<ApiResponse<OrganizationResponse>> {
    const response = await apiClient.get<ApiResponse<OrganizationResponse>>(
      '/organizations/current'
    );
    return response.data;
  },

  /**
   * Retrieves specific organization details by ID.
   * GET /api/v1/organizations/{id}
   */
  async getOrganization(id: string): Promise<ApiResponse<OrganizationResponse>> {
    const response = await apiClient.get<ApiResponse<OrganizationResponse>>(
      `/organizations/${id}`
    );
    return response.data;
  },

  /**
   * Creates a new tenant organization.
   * POST /api/v1/organizations
   */
  async createOrganization(
    data: OrganizationCreate
  ): Promise<ApiResponse<OrganizationResponse>> {
    const response = await apiClient.post<ApiResponse<OrganizationResponse>>(
      '/organizations',
      data
    );
    return response.data;
  },

  /**
   * Updates organization settings, metadata, or active status.
   * PATCH /api/v1/organizations/{id}
   */
  async updateOrganization(
    id: string,
    data: OrganizationUpdate
  ): Promise<ApiResponse<OrganizationResponse>> {
    const response = await apiClient.patch<ApiResponse<OrganizationResponse>>(
      `/organizations/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Soft deletes or deactivates an organization tenant.
   * DELETE /api/v1/organizations/{id}
   */
  async deleteOrganization(
    id: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(
      `/organizations/${id}`
    );
    return response.data;
  },
};

export default orgService;
