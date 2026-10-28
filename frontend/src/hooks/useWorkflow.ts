/**
 * KEEP Enterprise Platform — Workflow Automation & Notifications Custom Hook.
 * Phase 3.4 State Management and API Integration.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { useCallback, useEffect, useState } from 'react';
import {
  workflowService,
  type ExecutionQueryParams,
  type NotificationQueryParams,
  type WorkflowQueryParams,
} from '@/services/workflowService';
import type {
  ApprovalDecision,
  NotificationItem,
  NotificationPreferenceItem,
  NotificationPreferenceUpdatePayload,
  WorkflowAnalyticsData,
  WorkflowApprovalItem,
  WorkflowCreatePayload,
  WorkflowExecutionItem,
  WorkflowItem,
  WorkflowTemplateItem,
  WorkflowUpdatePayload,
} from '@/types/workflow';

export function useWorkflow() {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [totalWorkflows, setTotalWorkflows] = useState<number>(0);
  const [activeWorkflow, setActiveWorkflow] = useState<WorkflowItem | null>(null);
  const [executions, setExecutions] = useState<WorkflowExecutionItem[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<WorkflowApprovalItem[]>([]);
  const [templates, setTemplates] = useState<WorkflowTemplateItem[]>([]);
  const [analytics, setAnalytics] = useState<WorkflowAnalyticsData | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadNotificationsCount, setUnreadNotificationsCount] = useState<number>(0);
  const [preferences, setPreferences] = useState<NotificationPreferenceItem[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ==========================================================================
  // Workflows CRUD & Execution
  // ==========================================================================

  const fetchWorkflows = useCallback(async (params?: WorkflowQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const res = await workflowService.getWorkflows(params);
      if (res.data) {
        setWorkflows(res.data.items || []);
        setTotalWorkflows(res.data.total || 0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workflows';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchWorkflow = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await workflowService.getWorkflow(id);
      if (res.data) {
        setActiveWorkflow(res.data);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workflow details';
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const createWorkflow = useCallback(
    async (payload: WorkflowCreatePayload) => {
      try {
        setLoading(true);
        setError(null);
        const res = await workflowService.createWorkflow(payload);
        if (res.data) {
          setWorkflows((prev) => [res.data, ...prev]);
          setTotalWorkflows((prev) => prev + 1);
        }
        return res.data;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to create workflow';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const updateWorkflow = useCallback(
    async (id: string, payload: WorkflowUpdatePayload) => {
      try {
        setLoading(true);
        setError(null);
        const res = await workflowService.updateWorkflow(id, payload);
        if (res.data) {
          setWorkflows((prev) => prev.map((w) => (w.id === id ? res.data : w)));
          if (activeWorkflow?.id === id) {
            setActiveWorkflow(res.data);
          }
        }
        return res.data;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to update workflow';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [activeWorkflow]
  );

  const deleteWorkflow = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      await workflowService.deleteWorkflow(id);
      setWorkflows((prev) => prev.filter((w) => w.id !== id));
      setTotalWorkflows((prev) => Math.max(0, prev - 1));
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete workflow';
      setError(msg);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const executeWorkflow = useCallback(
    async (id: string, payload?: { context_data?: Record<string, unknown>; trigger_metadata?: Record<string, unknown> }) => {
      try {
        setLoading(true);
        setError(null);
        const res = await workflowService.executeWorkflow(id, payload);
        if (res.data) {
          setExecutions((prev) => [res.data, ...prev]);
          // Refresh workflow status counter
          setWorkflows((prev) =>
            prev.map((w) => (w.id === id ? { ...w, execution_count: w.execution_count + 1 } : w))
          );
        }
        return res.data;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to execute workflow';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const fetchExecutions = useCallback(async (id: string, params?: ExecutionQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const res = await workflowService.getWorkflowExecutions(id, params);
      if (res.data) {
        setExecutions(res.data.items || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workflow executions';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Approvals
  // ==========================================================================

  const fetchPendingApprovals = useCallback(async () => {
    try {
      const res = await workflowService.getPendingApprovals();
      if (res.data) {
        setPendingApprovals(res.data.items || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch pending approvals';
      setError(msg);
    }
  }, []);

  const decideApproval = useCallback(
    async (approvalId: string, decision: ApprovalDecision, comments?: string) => {
      try {
        setLoading(true);
        setError(null);
        const res = await workflowService.decideApproval(approvalId, { decision, comments });
        if (res.data) {
          setPendingApprovals((prev) => prev.filter((a) => a.id !== approvalId));
        }
        return res.data;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to decide approval';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // ==========================================================================
  // Templates & Analytics
  // ==========================================================================

  const fetchTemplates = useCallback(async () => {
    try {
      const res = await workflowService.getWorkflowTemplates();
      if (res.data) {
        setTemplates(res.data.items || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workflow templates';
      setError(msg);
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await workflowService.getWorkflowAnalytics();
      if (res.data) {
        setAnalytics(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch workflow analytics';
      setError(msg);
    }
  }, []);

  // ==========================================================================
  // Notifications & Channel Preferences
  // ==========================================================================

  const fetchNotifications = useCallback(async (params?: NotificationQueryParams) => {
    try {
      const res = await workflowService.getNotifications(params);
      if (res.data) {
        setNotifications(res.data.items || []);
        setUnreadNotificationsCount(res.data.unread_count || 0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch notifications';
      setError(msg);
    }
  }, []);

  const markNotificationRead = useCallback(async (notificationId: string) => {
    try {
      const res = await workflowService.markNotificationRead(notificationId);
      if (res.data) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
        );
        setUnreadNotificationsCount((prev) => Math.max(0, prev - 1));
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to mark notification as read';
      setError(msg);
    }
  }, []);

  const markAllNotificationsRead = useCallback(async () => {
    try {
      const res = await workflowService.markAllNotificationsRead();
      if (res.data?.success) {
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        setUnreadNotificationsCount(0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to mark all notifications as read';
      setError(msg);
    }
  }, []);

  const fetchNotificationPreferences = useCallback(async () => {
    try {
      const res = await workflowService.getNotificationPreferences();
      if (res.data) {
        setPreferences(res.data.items || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch notification preferences';
      setError(msg);
    }
  }, []);

  const updateNotificationPreferences = useCallback(
    async (payload: NotificationPreferenceUpdatePayload) => {
      try {
        setLoading(true);
        setError(null);
        const res = await workflowService.updateNotificationPreferences(payload);
        if (res.data) {
          setPreferences((prev) =>
            prev.map((p) => (p.category === payload.category ? res.data : p))
          );
        }
        return res.data;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to update notification preferences';
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Initial load
  useEffect(() => {
    fetchWorkflows();
    fetchPendingApprovals();
    fetchTemplates();
    fetchAnalytics();
    fetchNotifications();
    fetchNotificationPreferences();
  }, [
    fetchWorkflows,
    fetchPendingApprovals,
    fetchTemplates,
    fetchAnalytics,
    fetchNotifications,
    fetchNotificationPreferences,
  ]);

  return {
    workflows,
    totalWorkflows,
    activeWorkflow,
    executions,
    pendingApprovals,
    templates,
    analytics,
    notifications,
    unreadNotificationsCount,
    preferences,
    loading,
    error,
    fetchWorkflows,
    fetchWorkflow,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    executeWorkflow,
    fetchExecutions,
    fetchPendingApprovals,
    decideApproval,
    fetchTemplates,
    fetchAnalytics,
    fetchNotifications,
    markNotificationRead,
    markAllNotificationsRead,
    fetchNotificationPreferences,
    updateNotificationPreferences,
  };
}
