/**
 * KEEP Enterprise Platform — Security Audit Log API Service.
 * Interacts with backend endpoint GET /api/v1/audit/logs (Phase 1.6).
 */

import { apiClient, unwrapData } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type { AuditLogEntry, AuditLogQueryParams } from '@/types/audit';

export const auditService = {
  /**
   * Fetches paginated security and authorization audit event records.
   */
  async getAuditLogs(
    params?: AuditLogQueryParams
  ): Promise<ApiResponse<PaginatedData<AuditLogEntry>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<AuditLogEntry>>>(
      '/api/v1/audit/logs',
      {
        params: {
          page: params?.page ?? 1,
          page_size: params?.page_size ?? 20,
          action: params?.action,
          resource_type: params?.resource_type,
          user_id: params?.user_id,
        },
      }
    );
    return response.data;
  },

  /**
   * Convenience unwrap helper returning paginated items directly.
   */
  async getAuditLogsData(
    params?: AuditLogQueryParams
  ): Promise<PaginatedData<AuditLogEntry>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<AuditLogEntry>>>(
      '/api/v1/audit/logs',
      { params }
    );
    return unwrapData(response);
  },
};
