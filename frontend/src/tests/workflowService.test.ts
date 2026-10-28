/**
 * Phase 3.4 Workflow Automation & Notifications API Client Service Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { workflowService } from '@/services/workflowService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Phase 3.4 Workflow Automation Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('createWorkflow() sends payload to /api/v1/workflows', async () => {
    const mockWorkflow = {
      id: 'wf-101',
      name: 'Test Workflow',
      trigger_type: 'document_created',
      is_active: true,
      steps: [],
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Created', data: mockWorkflow },
    });

    const res = await workflowService.createWorkflow({
      name: 'Test Workflow',
      trigger_type: 'document_created',
      steps: [
        {
          step_order: 1,
          name: 'Notify User',
          action_type: 'send_notification',
          action_config: { channel: 'in_app' },
        },
      ],
    });

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/workflows', expect.objectContaining({
      name: 'Test Workflow',
      trigger_type: 'document_created',
    }));
    expect(res.data).toEqual(mockWorkflow);
  });

  it('getWorkflows() passes query parameters to /api/v1/workflows', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { items: [], total: 0 } },
    });

    await workflowService.getWorkflows({ is_active: true, trigger_type: 'document_created' });

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/workflows', {
      params: { is_active: true, trigger_type: 'document_created' },
    });
  });

  it('getWorkflow() retrieves single workflow by ID', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { id: 'wf-101', name: 'Test' } },
    });

    const res = await workflowService.getWorkflow('wf-101');
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/workflows/wf-101');
    expect(res.data).toEqual({ id: 'wf-101', name: 'Test' });
  });

  it('executeWorkflow() posts trigger request to /api/v1/workflows/{id}/execute', async () => {
    const mockExecution = {
      id: 'exec-1',
      workflow_id: 'wf-101',
      status: 'completed',
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockExecution },
    });

    const res = await workflowService.executeWorkflow('wf-101', {
      context_data: { document_id: 'doc-123' },
    });

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/workflows/wf-101/execute', {
      context_data: { document_id: 'doc-123' },
    });
    expect(res.data).toEqual(mockExecution);
  });

  it('getPendingApprovals() calls /api/v1/workflows/approvals/pending', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { items: [], total: 0 } },
    });

    await workflowService.getPendingApprovals();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/workflows/approvals/pending');
  });

  it('decideApproval() posts decision payload to /api/v1/workflows/approvals/{id}/decide', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { id: 'appr-1', decision: 'approved' } },
    });

    await workflowService.decideApproval('appr-1', {
      decision: 'approved',
      comments: 'Looks good.',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/workflows/approvals/appr-1/decide', {
      decision: 'approved',
      comments: 'Looks good.',
    });
  });

  it('getWorkflowTemplates() calls /api/v1/workflows/templates', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { items: [], total: 0 } },
    });

    await workflowService.getWorkflowTemplates();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/workflows/templates');
  });

  it('getWorkflowAnalytics() calls /api/v1/workflows/analytics', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { success_rate: 99.5, total_workflows: 10 } },
    });

    const res = await workflowService.getWorkflowAnalytics();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/workflows/analytics');
    expect(res.data).toEqual({ success_rate: 99.5, total_workflows: 10 });
  });

  it('getNotifications() fetches notifications with query filter', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { items: [], total: 0, unread_count: 0 } },
    });

    await workflowService.getNotifications({ is_read: false, category: 'workflow' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/notifications', {
      params: { is_read: false, category: 'workflow' },
    });
  });

  it('markNotificationRead() posts to /api/v1/notifications/{id}/read', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { id: 'notif-1', is_read: true } },
    });

    await workflowService.markNotificationRead('notif-1');
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/notifications/notif-1/read');
  });

  it('markAllNotificationsRead() posts to /api/v1/notifications/read-all', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { success: true, marked_count: 5 } },
    });

    await workflowService.markAllNotificationsRead();
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/notifications/read-all');
  });

  it('notification preferences get and update API calls', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { items: [] } },
    });
    await workflowService.getNotificationPreferences();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/notifications/preferences');

    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { category: 'workflow', email: true } },
    });
    await workflowService.updateNotificationPreferences({ category: 'workflow', email: true });
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/notifications/preferences', {
      category: 'workflow',
      email: true,
    });
  });
});
