/**
 * KEEP Enterprise Platform — Activity Log / Audit Trail API Client Service.
 * Connects frontend security views to backend `activity_logs` persistence endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type { ActivityLog, ActivityLogFilterParams } from '@/types/activity';

export const activityService = {
  /**
   * List security audit logs with pagination and filters.
   */
  async listActivityLogs(
    params?: ActivityLogFilterParams
  ): Promise<ApiResponse<PaginatedData<ActivityLog>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<ActivityLog>>>(
      '/activity-logs',
      { params }
    );
    return response.data;
  },
};
