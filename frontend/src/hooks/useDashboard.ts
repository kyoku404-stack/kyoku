/**
 * KEEP Enterprise Platform — Dashboard Custom Hooks.
 * Implements widget-level independent data hooks conforming to
 * docs/Architecture/dashboard-architecture.md Section 4.2.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardService } from '@/services/dashboardService';
import type {
  DashboardSummary,
  ActivityEvent,
  ProjectSummary,
  DocumentSummary,
  NotificationItem,
  DashboardAnalyticsSummary,
  GlobalSearchResultItem,
  DocumentReference,
} from '@/types/dashboard';
import { useAuthStore } from '@/store/useAuthStore';

// =============================================================================
// 1. useDashboardSummary
// =============================================================================

export function useDashboardSummary() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getDashboardSummary();
      if (response.success && response.data) {
        setSummary(response.data);
      } else {
        setError('Failed to load dashboard summary.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching dashboard summary');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return { summary, isLoading, error, refresh: fetchSummary };
}

// =============================================================================
// 2. useActivityFeed
// =============================================================================

export function useActivityFeed(initialFilter: string = 'all') {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [filter, setFilter] = useState<string>(initialFilter);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getActivityFeed({
        page,
        page_size: 15,
        filter: filter !== 'all' ? filter : undefined,
      });
      if (response.success && response.data) {
        setEvents(response.data.items);
        setTotal(response.data.total);
        setTotalPages(response.data.total_pages || 1);
      } else {
        setError('Failed to load activity feed.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching activity feed');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, page, filter]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const changeFilter = (newFilter: string) => {
    setFilter(newFilter);
    setPage(1);
  };

  return {
    events,
    filter,
    page,
    total,
    totalPages,
    isLoading,
    error,
    changeFilter,
    setPage,
    refresh: fetchEvents,
  };
}

// =============================================================================
// 3. useRecentProjects
// =============================================================================

export function useRecentProjects(limit: number = 6) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getRecentProjects(limit);
      if (response.success && response.data) {
        setProjects(response.data);
      } else {
        setError('Failed to load recent projects.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching recent projects');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, limit]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return { projects, isLoading, error, refresh: fetchProjects };
}

// =============================================================================
// 4. useRecentDocuments
// =============================================================================

export function useRecentDocuments(limit: number = 8) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getRecentDocuments(limit);
      if (response.success && response.data) {
        setDocuments(response.data);
      } else {
        setError('Failed to load recent documents.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching recent documents');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, limit]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return { documents, isLoading, error, refresh: fetchDocuments };
}

// =============================================================================
// 5. useNotifications
// =============================================================================

export function useNotifications(initialUnreadOnly: boolean = false, initialPageSize: number = 15) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [unreadOnly, setUnreadOnly] = useState<boolean>(initialUnreadOnly);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(initialPageSize);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getNotifications({
        page,
        page_size: pageSize,
        unread_only: unreadOnly,
      });
      if (response.success && response.data) {
        const normalized = (response.data.items || []).map((n) => ({
          ...n,
          category: n.category || n.type,
          message: n.message || n.body,
          link_url: n.link_url || n.action_url,
        }));
        setNotifications(normalized);
        setTotalPages(response.data.total_pages || 1);
        const unread = normalized.filter((n) => !n.is_read).length;
        setUnreadCount(unread);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching notifications');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, page, pageSize, unreadOnly]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const markAsRead = async (id: string) => {
    try {
      const res = await dashboardService.markNotificationRead(id);
      if (res.success) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
        setUnreadCount((c) => Math.max(0, c - 1));
      }
    } catch {
      // optimistic error handling
    }
  };

  const markAllAsRead = async () => {
    try {
      const res = await dashboardService.markAllNotificationsRead();
      if (res.success) {
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        setUnreadCount(0);
      }
    } catch {
      // error fallback
    }
  };

  return {
    notifications,
    unreadCount,
    unreadOnly,
    setUnreadOnly,
    page,
    setPage,
    totalPages,
    isLoading,
    error,
    markAsRead,
    markAllAsRead,
    refresh: fetchNotifications,
  };
}

// =============================================================================
// 6. useAnalyticsSummary
// =============================================================================

export function useAnalyticsSummary(initialPeriod: 'week' | 'month' | 'quarter' | 'year' = 'week') {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [period, setPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>(initialPeriod);
  const [analytics, setAnalytics] = useState<DashboardAnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getAnalyticsSummary(period);
      if (response.success && response.data) {
        setAnalytics(response.data);
      } else {
        setError('Failed to load analytics summary.');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error fetching analytics summary');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, period]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return {
    analytics,
    period,
    setPeriod,
    isLoading,
    error,
    refresh: fetchAnalytics,
  };
}

// =============================================================================
// 7. useGlobalSearch
// =============================================================================

export function useGlobalSearch(debounceMs: number = 300) {
  const [query, setQuery] = useState('');
  const [type, setType] = useState<'all' | 'project' | 'document' | 'user' | 'team'>('all');
  const [results, setResults] = useState<GlobalSearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const executeSearch = useCallback(async (q: string, t: typeof type) => {
    if (!q.trim()) {
      setResults([]);
      setTotal(0);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.globalSearch({ q, type: t });
      if (response.success && response.data) {
        setResults(response.data.items || []);
        setTotal(response.data.total || 0);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Search request failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!query.trim()) {
      setResults([]);
      setTotal(0);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    debounceTimerRef.current = setTimeout(() => {
      executeSearch(query, type);
    }, debounceMs);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [query, type, debounceMs, executeSearch]);

  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setTotal(0);
  }, []);

  return {
    query,
    setQuery,
    type,
    setType,
    results,
    total,
    totalCount: total,
    isLoading,
    isSearching: isLoading,
    error,
    executeSearch,
    clearSearch,
  };
}

// =============================================================================
// 8. useAIAssistant
// =============================================================================

export function useAIAssistant() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<'IDLE' | 'TYPING' | 'LOADING' | 'STREAMING' | 'COMPLETE' | 'ERROR'>('IDLE');
  const [streamingResponse, setStreamingResponse] = useState('');
  const [sources, setSources] = useState<DocumentReference[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const submitQuery = useCallback(async (customQuery?: string) => {
    const q = (customQuery || query).trim();
    if (!q) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setStatus('LOADING');
    setStreamingResponse('');
    setSources([]);
    setError(null);

    await dashboardService.streamAIQuery(
      { query: q, stream: true },
      {
        onToken: (token) => {
          setStatus('STREAMING');
          setStreamingResponse((prev) => prev + token);
        },
        onDone: (doneData) => {
          setStatus('COMPLETE');
          setSources(doneData.sources || []);
        },
        onError: (err) => {
          setStatus('ERROR');
          setError(err.message || 'AI Assistant connection error');
        },
      },
      controller.signal
    );
  }, [query]);

  const resetAssistant = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setQuery('');
    setStatus('IDLE');
    setStreamingResponse('');
    setSources([]);
    setError(null);
  }, []);

  return {
    query,
    setQuery,
    status,
    streamingResponse,
    sources,
    error,
    submitQuery,
    resetAssistant,
  };
}
