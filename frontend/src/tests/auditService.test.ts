import { describe, it, expect, vi, beforeEach } from 'vitest';
import { auditService } from '@/services/auditService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
    },
  };
});

describe('Phase 1.6 AuditService API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('queries /api/v1/audit/logs with pagination and filter parameters', async () => {
    const mockApiResponse = {
      data: {
        success: true,
        message: 'Audit logs retrieved successfully',
        data: {
          items: [
            {
              id: 'audit-log-1',
              organization_id: 'org-uuid-1',
              user_id: 'user-uuid-1',
              action: 'PERMISSION_GRANTED',
              resource_type: 'document',
              resource_id: 'doc-uuid-10',
              details: "Action 'document.read' granted for role Member",
              ip_address: '127.0.0.1',
              created_at: '2026-10-12T10:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockApiResponse);

    const result = await auditService.getAuditLogs({
      page: 1,
      page_size: 20,
      action: 'PERMISSION_GRANTED',
      resource_type: 'document',
    });

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/audit/logs', {
      params: {
        page: 1,
        page_size: 20,
        action: 'PERMISSION_GRANTED',
        resource_type: 'document',
        user_id: undefined,
      },
    });

    expect(result.success).toBe(true);
    expect(result.data.items).toHaveLength(1);
    expect(result.data.items[0].action).toBe('PERMISSION_GRANTED');
  });

  it('unwraps data payload via getAuditLogsData helper', async () => {
    const mockApiResponse = {
      data: {
        success: true,
        message: 'Success',
        data: {
          items: [
            {
              id: 'audit-log-2',
              organization_id: 'org-uuid-1',
              action: 'PERMISSION_DENIED',
              resource_type: 'analytics',
              created_at: '2026-10-12T10:05:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockApiResponse);

    const data = await auditService.getAuditLogsData({ page: 1 });
    expect(data.items).toHaveLength(1);
    expect(data.items[0].action).toBe('PERMISSION_DENIED');
  });
});
