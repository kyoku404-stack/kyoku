/**
 * KEEP Enterprise Platform — Dashboard API Client Service.
 * Implements client bindings for all Phase 1.7 Dashboard APIs defined in
 * docs/Architecture/dashboard-architecture.md Section 3 and docs/API/api-contract.md Section 5.
 */

import { apiClient, unwrapData } from './api';
import { CONFIG } from '@/constants/config';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  DashboardSummary,
  ActivityEvent,
  ActivityFeedFilterParams,
  ProjectSummary,
  DocumentSummary,
  NotificationItem,
  NotificationQueryParams,
  NotificationReadAllResponse,
  DashboardAnalyticsSummary,
  GlobalSearchResponse,
  GlobalSearchParams,
  AIQueryRequest,
  AIStreamDone,
} from '@/types/dashboard';

export const dashboardService = {
  /**
   * Retrieves the authenticated user's personalized dashboard summary and KPI counters.
   * Cached in backend Redis for 60s.
   */
  async getDashboardSummary(): Promise<ApiResponse<DashboardSummary>> {
    const response = await apiClient.get<ApiResponse<DashboardSummary>>('/api/v1/dashboard');
    return response.data;
  },

  async getDashboardSummaryData(): Promise<DashboardSummary> {
    const response = await apiClient.get<ApiResponse<DashboardSummary>>('/api/v1/dashboard');
    return unwrapData(response);
  },

  /**
   * Retrieves paginated organizational activity feed visible to the authenticated user.
   */
  async getActivityFeed(
    params?: ActivityFeedFilterParams
  ): Promise<ApiResponse<PaginatedData<ActivityEvent>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<ActivityEvent>>>(
      '/api/v1/activity',
      {
        params: {
          page: params?.page ?? 1,
          page_size: params?.page_size ?? 20,
          filter: params?.filter || 'all',
        },
      }
    );
    return response.data;
  },

  async getActivityFeedData(
    params?: ActivityFeedFilterParams
  ): Promise<PaginatedData<ActivityEvent>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<ActivityEvent>>>(
      '/api/v1/activity',
      { params }
    );
    return unwrapData(response);
  },

  /**
   * Retrieves recently updated projects accessible to the caller.
   */
  async getRecentProjects(limit: number = 6): Promise<ApiResponse<ProjectSummary[]>> {
    const response = await apiClient.get<ApiResponse<ProjectSummary[]>>(
      '/api/v1/projects/recent',
      { params: { limit } }
    );
    return response.data;
  },

  async getRecentProjectsData(limit: number = 6): Promise<ProjectSummary[]> {
    const response = await apiClient.get<ApiResponse<ProjectSummary[]>>(
      '/api/v1/projects/recent',
      { params: { limit } }
    );
    return unwrapData(response);
  },

  /**
   * Retrieves recently accessed or uploaded documents visible to the caller.
   */
  async getRecentDocuments(limit: number = 8): Promise<ApiResponse<DocumentSummary[]>> {
    const response = await apiClient.get<ApiResponse<DocumentSummary[]>>(
      '/api/v1/documents/recent',
      { params: { limit } }
    );
    return response.data;
  },

  async getRecentDocumentsData(limit: number = 8): Promise<DocumentSummary[]> {
    const response = await apiClient.get<ApiResponse<DocumentSummary[]>>(
      '/api/v1/documents/recent',
      { params: { limit } }
    );
    return unwrapData(response);
  },

  /**
   * Retrieves paginated user notifications.
   */
  async getNotifications(
    params?: NotificationQueryParams
  ): Promise<ApiResponse<PaginatedData<NotificationItem>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<NotificationItem>>>(
      '/api/v1/notifications',
      {
        params: {
          page: params?.page ?? 1,
          page_size: params?.page_size ?? 20,
          unread_only: params?.unread_only ?? false,
        },
      }
    );
    return response.data;
  },

  async getNotificationsData(
    params?: NotificationQueryParams
  ): Promise<PaginatedData<NotificationItem>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<NotificationItem>>>(
      '/api/v1/notifications',
      { params }
    );
    return unwrapData(response);
  },

  /**
   * Marks a single notification as read.
   */
  async markNotificationRead(id: string): Promise<ApiResponse<NotificationItem>> {
    const response = await apiClient.patch<ApiResponse<NotificationItem>>(
      `/api/v1/notifications/${id}/read`
    );
    return response.data;
  },

  /**
   * Marks all notifications as read for the authenticated caller.
   */
  async markAllNotificationsRead(): Promise<ApiResponse<NotificationReadAllResponse>> {
    const response = await apiClient.post<ApiResponse<NotificationReadAllResponse>>(
      '/api/v1/notifications/read-all'
    );
    return response.data;
  },

  /**
   * Retrieves aggregated time-series analytics for OrgAdmin and SuperAdmin.
   */
  async getAnalyticsSummary(
    period: 'week' | 'month' | 'quarter' | 'year' = 'week'
  ): Promise<ApiResponse<DashboardAnalyticsSummary>> {
    const response = await apiClient.get<ApiResponse<DashboardAnalyticsSummary>>(
      '/api/v1/analytics/summary',
      { params: { period } }
    );
    return response.data;
  },

  async getAnalyticsSummaryData(
    period: 'week' | 'month' | 'quarter' | 'year' = 'week'
  ): Promise<DashboardAnalyticsSummary> {
    const response = await apiClient.get<ApiResponse<DashboardAnalyticsSummary>>(
      '/api/v1/analytics/summary',
      { params: { period } }
    );
    return unwrapData(response);
  },

  /**
   * Debounced multi-entity full-text global search across projects, documents, users, and teams.
   */
  async globalSearch(params: GlobalSearchParams): Promise<ApiResponse<GlobalSearchResponse>> {
    const response = await apiClient.get<ApiResponse<GlobalSearchResponse>>('/api/v1/search', {
      params: {
        q: params.q,
        type: params.type || 'all',
        page: params.page ?? 1,
        page_size: params.page_size ?? 10,
      },
    });
    return response.data;
  },

  async globalSearchData(params: GlobalSearchParams): Promise<GlobalSearchResponse> {
    const response = await apiClient.get<ApiResponse<GlobalSearchResponse>>('/api/v1/search', {
      params,
    });
    return unwrapData(response);
  },

  /**
   * Connects to Server-Sent Events (SSE) AI assistant stream (`POST /api/v1/ai/query`).
   * Handles token-by-token streaming, source citations on completion, and error states.
   */
  async streamAIQuery(
    request: AIQueryRequest,
    callbacks: {
      onToken: (token: string) => void;
      onDone: (doneData: AIStreamDone) => void;
      onError: (err: Error) => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    const token = localStorage.getItem('keep_auth_token');
    const url = `${CONFIG.API_BASE_URL}/api/v1/ai/query`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: request.query,
          context: request.context || null,
          stream: true,
        }),
        signal,
      });

      if (!response.ok) {
        let errMessage = `AI Assistant query failed with HTTP status ${response.status}`;
        try {
          const errData = await response.json();
          if (errData?.error?.message) {
            errMessage = errData.error.message;
          }
        } catch {
          // ignore fallback
        }
        throw new Error(errMessage);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('ReadableStream not supported by response');
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let isDone = false;

      while (!isDone) {
        const { value, done } = await reader.read();
        if (done) {
          isDone = true;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = 'message';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.replace('event:', '').trim();
          } else if (trimmed.startsWith('data:')) {
            const rawData = trimmed.replace('data:', '').trim();
            try {
              const parsed = JSON.parse(rawData);

              if (currentEvent === 'token' && typeof parsed.token === 'string') {
                callbacks.onToken(parsed.token);
              } else if (currentEvent === 'done') {
                callbacks.onDone({
                  sources: parsed.sources || [],
                  query_id: parsed.query_id,
                });
              } else if (currentEvent === 'error') {
                callbacks.onError(new Error(parsed.message || 'AI Assistant query error'));
              }
            } catch {
              // Non-JSON SSE payload fallback
              if (currentEvent === 'token') {
                callbacks.onToken(rawData);
              }
            }
          }
        }
      }
    } catch (err: unknown) {
      if (signal?.aborted) return;
      callbacks.onError(err instanceof Error ? err : new Error(String(err)));
    }
  },
};
