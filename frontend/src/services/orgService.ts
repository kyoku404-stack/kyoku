/**
 * KEEP Enterprise Platform — Organization & Tenant Service Client.
 * Connects to /api/v1/organizations endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type { OrganizationResponse } from '@/types/organization';

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
};

export default orgService;
