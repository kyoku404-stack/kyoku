/**
 * KEEP Enterprise Platform — Workflow Automation & Notifications API Client Service.
 * Phase 3.4 Domain API Service aligned with docs/api/api-contract.md Section 16.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  WorkflowAnalyticsData,
  WorkflowApprovalDecisionPayload,
  WorkflowApprovalItem,
  WorkflowCreatePayload,
  WorkflowExecutionItem,
  WorkflowItem,
  WorkflowTemplateItem,
  WorkflowUpdatePayload,
  NotificationItem,
  NotificationPreferenceItem,
  NotificationPreferenceUpdatePayload,
} from '@/types/workflow';

export interface WorkflowQueryParams {
  is_active?: boolean;
  trigger_type?: string;
}

export interface ExecutionQueryParams {
  limit?: number;
  offset?: number;
}

export interface NotificationQueryParams {
  is_read?: boolean;
  category?: string;
  limit?: number;
}

export const workflowService = {
  /**
   * Create a new automated workflow definition.
   */
  async createWorkflow(payload: WorkflowCreatePayload): Promise<ApiResponse<WorkflowItem>> {
    const response = await apiClient.post<ApiResponse<WorkflowItem>>('/api/v1/workflows', payload);
    return response.data;
  },

  /**
   * List workflows with optional active/trigger filters.
   */
  async getWorkflows(params?: WorkflowQueryParams): Promise<ApiResponse<{ items: WorkflowItem[]; total: number }>> {
    const response = await apiClient.get<ApiResponse<{ items: WorkflowItem[]; total: number }>>('/api/v1/workflows', {
      params,
    });
    return response.data;
  },

  /**
   * Get workflow details by ID including ordered steps.
   */
  async getWorkflow(id: string): Promise<ApiResponse<WorkflowItem>> {
    const response = await apiClient.get<ApiResponse<WorkflowItem>>(`/api/v1/workflows/${id}`);
    return response.data;
  },

  /**
   * Update a workflow definition.
   */
  async updateWorkflow(id: string, payload: WorkflowUpdatePayload): Promise<ApiResponse<WorkflowItem>> {
    const response = await apiClient.put<ApiResponse<WorkflowItem>>(`/api/v1/workflows/${id}`, payload);
    return response.data;
  },

  /**
   * Delete a workflow definition.
   */
  async deleteWorkflow(id: string): Promise<ApiResponse<{ success: boolean; message: string }>> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean; message: string }>>(`/api/v1/workflows/${id}`);
    return response.data;
  },

  /**
   * Manually trigger an execution of a workflow.
   */
  async executeWorkflow(
    id: string,
    payload?: { context_data?: Record<string, unknown>; trigger_metadata?: Record<string, unknown> }
  ): Promise<ApiResponse<WorkflowExecutionItem>> {
    const response = await apiClient.post<ApiResponse<WorkflowExecutionItem>>(
      `/api/v1/workflows/${id}/execute`,
      payload || {}
    );
    return response.data;
  },

  /**
   * List execution history for a workflow.
   */
  async getWorkflowExecutions(
    id: string,
    params?: ExecutionQueryParams
  ): Promise<ApiResponse<{ items: WorkflowExecutionItem[]; total: number }>> {
    const response = await apiClient.get<ApiResponse<{ items: WorkflowExecutionItem[]; total: number }>>(
      `/api/v1/workflows/${id}/executions`,
      { params }
    );
    return response.data;
  },

  /**
   * Get detailed status and step runs of an execution.
   */
  async getExecutionDetails(executionId: string): Promise<ApiResponse<WorkflowExecutionItem>> {
    const response = await apiClient.get<ApiResponse<WorkflowExecutionItem>>(
      `/api/v1/workflows/executions/${executionId}`
    );
    return response.data;
  },

  /**
   * List all pending human-in-the-loop approvals.
   */
  async getPendingApprovals(): Promise<ApiResponse<{ items: WorkflowApprovalItem[]; total: number }>> {
    const response = await apiClient.get<ApiResponse<{ items: WorkflowApprovalItem[]; total: number }>>(
      '/api/v1/workflows/approvals/pending'
    );
    return response.data;
  },

  /**
   * Submit decision (approve or reject) for a pending approval step.
   */
  async decideApproval(
    approvalId: string,
    payload: WorkflowApprovalDecisionPayload
  ): Promise<ApiResponse<WorkflowApprovalItem>> {
    const response = await apiClient.post<ApiResponse<WorkflowApprovalItem>>(
      `/api/v1/workflows/approvals/${approvalId}/decide`,
      payload
    );
    return response.data;
  },

  /**
   * List available pre-configured workflow templates.
   */
  async getWorkflowTemplates(): Promise<ApiResponse<{ items: WorkflowTemplateItem[]; total: number }>> {
    const response = await apiClient.get<ApiResponse<{ items: WorkflowTemplateItem[]; total: number }>>(
      '/api/v1/workflows/templates'
    );
    return response.data;
  },

  /**
   * Get aggregated workflow analytics metrics.
   */
  async getWorkflowAnalytics(): Promise<ApiResponse<WorkflowAnalyticsData>> {
    const response = await apiClient.get<ApiResponse<WorkflowAnalyticsData>>('/api/v1/workflows/analytics');
    return response.data;
  },

  /**
   * List user notifications with filtering.
   */
  async getNotifications(
    params?: NotificationQueryParams
  ): Promise<ApiResponse<{ items: NotificationItem[]; total: number; unread_count: number }>> {
    const response = await apiClient.get<ApiResponse<{ items: NotificationItem[]; total: number; unread_count: number }>>(
      '/api/v1/notifications',
      { params }
    );
    return response.data;
  },

  /**
   * Mark a single notification as read.
   */
  async markNotificationRead(notificationId: string): Promise<ApiResponse<NotificationItem>> {
    const response = await apiClient.post<ApiResponse<NotificationItem>>(`/api/v1/notifications/${notificationId}/read`);
    return response.data;
  },

  /**
   * Mark all notifications as read for current user.
   */
  async markAllNotificationsRead(): Promise<ApiResponse<{ success: boolean; marked_count: number }>> {
    const response = await apiClient.post<ApiResponse<{ success: boolean; marked_count: number }>>(
      '/api/v1/notifications/read-all'
    );
    return response.data;
  },

  /**
   * Retrieve multi-channel notification preferences.
   */
  async getNotificationPreferences(): Promise<ApiResponse<{ items: NotificationPreferenceItem[] }>> {
    const response = await apiClient.get<ApiResponse<{ items: NotificationPreferenceItem[] }>>(
      '/api/v1/notifications/preferences'
    );
    return response.data;
  },

  /**
   * Update notification channel delivery preferences.
   */
  async updateNotificationPreferences(
    payload: NotificationPreferenceUpdatePayload
  ): Promise<ApiResponse<NotificationPreferenceItem>> {
    const response = await apiClient.post<ApiResponse<NotificationPreferenceItem>>(
      '/api/v1/notifications/preferences',
      payload
    );
    return response.data;
  },
};
