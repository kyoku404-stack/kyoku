import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dashboardService } from '@/services/dashboardService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockEnvelope = <T,>(data: T) => ({
  data: {
    success: true,
    message: 'OK',
    data,
  },
});

describe('Phase 1.7 Dashboard Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches dashboard summary via GET /api/v1/dashboard', async () => {
    const mockSummary = {
      user: { id: 'u1', full_name: 'John Doe', email: 'john@example.com', role: 'OrgAdmin' },
      organization: { id: 'o1', name: 'Acme Corp', plan: 'enterprise' },
      kpi: {
        total_projects: 8,
        total_documents: 42,
        total_members: 15,
        upcoming_meetings: 3,
        storage_used_bytes: 1048576,
        storage_quota_bytes: 10737418240,
        ai_queries_today: 95,
      },
      greeting_time_of_day: 'morning' as const,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockEnvelope(mockSummary));

    const res = await dashboardService.getDashboardSummary();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/dashboard');
    expect(res.success).toBe(true);
    expect(res.data?.user.full_name).toBe('John Doe');
    expect(res.data?.kpi.total_projects).toBe(8);
  });

  it('fetches activity feed with filter params via GET /api/v1/activity', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(
      mockEnvelope({
        items: [
          {
            id: 'act-1',
            actor: { id: 'u1', full_name: 'John Doe' },
            action: 'uploaded',
            resource_type: 'document',
            resource_name: 'Q3_Report.pdf',
            occurred_at: '2026-10-15T10:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })
    );

    const res = await dashboardService.getActivityFeed({ page: 1, page_size: 10, filter: 'document' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/activity', {
      params: { page: 1, page_size: 10, filter: 'document' },
    });
    expect(res.success).toBe(true);
    expect(res.data?.items[0].resource_name).toBe('Q3_Report.pdf');
  });

  it('fetches recent projects via GET /api/v1/projects/recent', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(
      mockEnvelope([
        {
          id: 'proj-1',
          name: 'AI Retrieval Engine',
          status: 'active',
          priority: 'high',
          progress_percent: 75,
          team_members: [],
          document_count: 5,
          updated_at: '2026-10-15T08:00:00Z',
        },
      ])
    );

    const res = await dashboardService.getRecentProjects(5);
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects/recent', { params: { limit: 5 } });
    expect(res.success).toBe(true);
    expect(res.data?.[0].progress_percent).toBe(75);
  });

  it('fetches recent documents via GET /api/v1/documents/recent', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(
      mockEnvelope([
        {
          id: 'doc-1',
          title: 'Specs.docx',
          file_type: 'docx',
          file_size_bytes: 2048,
          uploaded_by: { id: 'u1', full_name: 'John Doe' },
          uploaded_at: '2026-10-15T09:00:00Z',
          last_accessed_at: '2026-10-15T09:30:00Z',
          ai_summary_available: true,
        },
      ])
    );

    const res = await dashboardService.getRecentDocuments(10);
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/documents/recent', { params: { limit: 10 } });
    expect(res.success).toBe(true);
    expect(res.data?.[0].ai_summary_available).toBe(true);
  });

  it('manages notifications via GET /notifications, PATCH /notifications/:id/read, POST /notifications/read-all', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(
      mockEnvelope({
        items: [{ id: 'notif-1', title: 'New Document', type: 'info', body: 'Ready', is_read: false, created_at: '2026-10-15T09:00:00Z' }],
        total: 1,
        page: 1,
        page_size: 15,
        total_pages: 1,
      })
    );

    const listRes = await dashboardService.getNotifications({ unread_only: true });
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/notifications', { params: { page: 1, page_size: 20, unread_only: true } });
    expect(listRes.success).toBe(true);

    vi.mocked(apiClient.patch).mockResolvedValueOnce(mockEnvelope({ id: 'notif-1', is_read: true }));
    const markRes = await dashboardService.markNotificationRead('notif-1');
    expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/notifications/notif-1/read');
    expect(markRes.success).toBe(true);

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockEnvelope({ updated_count: 5 }));
    const allRes = await dashboardService.markAllNotificationsRead();
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/notifications/read-all');
    expect(allRes.success).toBe(true);
  });

  it('fetches analytics summary via GET /api/v1/analytics/summary', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(
      mockEnvelope({
        period: 'month',
        documents_uploaded: [{ label: 'Week 1', value: 20 }],
        active_users: [{ label: 'Week 1', value: 45 }],
        new_members: [],
        project_distribution: [{ status: 'active', count: 12 }],
        ai_usage_trend: [],
        search_trend: [],
      })
    );

    const res = await dashboardService.getAnalyticsSummary('month');
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/analytics/summary', { params: { period: 'month' } });
    expect(res.success).toBe(true);
    expect(res.data?.documents_uploaded[0].value).toBe(20);
  });

  it('performs global search via GET /api/v1/search', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(
      mockEnvelope({
        query: 'retrieval',
        total: 1,
        items: [
          {
            type: 'project',
            id: 'proj-1',
            title: 'Knowledge Retrieval Engine',
            subtitle: 'AI & Ingestion',
            url: '/projects/proj-1',
            icon: 'folder',
            relevance_score: 0.95,
          },
        ],
      })
    );

    const res = await dashboardService.globalSearch({ q: 'retrieval', type: 'project' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/search', { params: { page: 1, page_size: 10, q: 'retrieval', type: 'project' } });
    expect(res.success).toBe(true);
    expect(res.data?.items[0].title).toBe('Knowledge Retrieval Engine');
  });
});
