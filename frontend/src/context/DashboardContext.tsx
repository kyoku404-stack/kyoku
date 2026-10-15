import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { dashboardService } from '@/services/dashboardService';
import type { DashboardSummary } from '@/types/dashboard';
import { useAuthStore } from '@/store/useAuthStore';

interface DashboardContextValue {
  summary: DashboardSummary | null;
  isLoading: boolean;
  error: string | null;
  refreshDashboard: () => Promise<void>;
  unreadNotificationCount: number;
  refreshNotifications: () => Promise<void>;
}

const DashboardContext = createContext<DashboardContextValue | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unreadNotificationCount, setUnreadNotificationCount] = useState(0);

  const fetchSummary = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await dashboardService.getDashboardSummary();
      if (response.success && response.data) {
        setSummary(response.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard summary');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  const fetchUnreadCount = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const response = await dashboardService.getNotifications({ page: 1, page_size: 1, unread_only: true });
      if (response.success && response.data) {
        setUnreadNotificationCount(response.data.total);
      }
    } catch {
      // Background count fetch failure non-fatal
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchSummary();
      fetchUnreadCount();
      // Optional polling every 60s for summary, 30s for notifications badge
      const timer = setInterval(() => {
        fetchUnreadCount();
      }, 30000);
      return () => clearInterval(timer);
    } else {
      setSummary(null);
      setUnreadNotificationCount(0);
    }
  }, [isAuthenticated, fetchSummary, fetchUnreadCount]);

  const value: DashboardContextValue = {
    summary,
    isLoading,
    error,
    refreshDashboard: fetchSummary,
    unreadNotificationCount,
    refreshNotifications: fetchUnreadCount,
  };

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
};

export const useDashboard = (): DashboardContextValue => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};

export const useDashboardContext = (): DashboardContextValue | undefined => {
  return useContext(DashboardContext);
};

