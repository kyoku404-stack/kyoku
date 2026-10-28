/**
 * Phase 3.4 Workflow Automation & Notifications Component Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import {
  WorkflowMetricsBanner,
  WorkflowListTable,
  CreateWorkflowModal,
  WorkflowApprovalQueue,
  NotificationCenterDrawer,
  NotificationPreferencesModal,
  WorkflowTemplateGallery,
  WorkflowAnalyticsDashboard,
} from '@/features/workflow';
import type {
  WorkflowAnalyticsData,
  WorkflowApprovalItem,
  WorkflowItem,
  WorkflowTemplateItem,
} from '@/types/workflow';

describe('Phase 3.4 Workflow Feature Components', () => {
  it('WorkflowMetricsBanner displays KPIs and triggers action callbacks', () => {
    const mockAnalytics: WorkflowAnalyticsData = {
      total_workflows: 8,
      active_workflows: 6,
      total_executions: 120,
      successful_executions: 118,
      failed_executions: 2,
      success_rate: 98.3,
      average_duration_ms: 1200,
      pending_approvals_count: 3,
      executions_by_day: [],
    };

    const onOpenCreate = vi.fn();
    const onOpenPrefs = vi.fn();
    const onOpenNotifs = vi.fn();
    const onRefresh = vi.fn();

    render(
      <WorkflowMetricsBanner
        analytics={mockAnalytics}
        pendingApprovalsCount={3}
        unreadNotificationsCount={5}
        onOpenCreateModal={onOpenCreate}
        onOpenPreferencesModal={onOpenPrefs}
        onOpenNotificationsDrawer={onOpenNotifs}
        onRefresh={onRefresh}
        isLoading={false}
      />
    );

    expect(screen.getByText('Workflow Automation & Intelligence')).toBeDefined();
    expect(screen.getByText('98.3%')).toBeDefined();
    expect(screen.getByText('6')).toBeDefined();
    expect(screen.getByText('120')).toBeDefined();

    fireEvent.click(screen.getByText('New Workflow'));
    expect(onOpenCreate).toHaveBeenCalled();

    fireEvent.click(screen.getByText('Preferences'));
    expect(onOpenPrefs).toHaveBeenCalled();
  });

  it('WorkflowListTable renders workflows and responds to execution and toggle', () => {
    const mockWorkflows: WorkflowItem[] = [
      {
        id: 'wf-1',
        organization_id: 'org-1',
        created_by_id: 'u-1',
        name: 'Auto-Tagger',
        description: 'Tags incoming documents',
        trigger_type: 'document_created',
        trigger_config: {},
        condition_rules: [],
        is_active: true,
        execution_count: 14,
        success_count: 14,
        created_at: '2026-10-28T00:00:00Z',
        updated_at: '2026-10-28T00:00:00Z',
        steps: [
          {
            step_order: 1,
            name: 'Extract Metadata',
            action_type: 'invoke_llm',
            action_config: {},
          },
        ],
      },
    ];

    const onExecute = vi.fn();
    const onToggle = vi.fn();
    const onDelete = vi.fn();
    const onSelect = vi.fn();

    render(
      <WorkflowListTable
        workflows={mockWorkflows}
        onExecute={onExecute}
        onToggleActive={onToggle}
        onDelete={onDelete}
        onSelectWorkflow={onSelect}
        isExecutingId={null}
      />
    );

    expect(screen.getByText('Auto-Tagger')).toBeDefined();
    expect(screen.getAllByText('Document Created').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByText('Run'));
    expect(onExecute).toHaveBeenCalledWith('wf-1');

    fireEvent.click(screen.getByText('Active'));
    expect(onToggle).toHaveBeenCalledWith('wf-1', true);
  });

  it('CreateWorkflowModal opens and validates required fields', async () => {
    const onClose = vi.fn();
    const onSubmit = vi.fn().mockResolvedValue({});

    render(
      <CreateWorkflowModal
        isOpen={true}
        onClose={onClose}
        onSubmit={onSubmit}
      />
    );

    expect(screen.getByText('Create Automated Workflow')).toBeDefined();

    // Type name
    const input = screen.getByPlaceholderText('e.g. Automated Document Classification & Alert');
    await act(async () => {
      fireEvent.change(input, { target: { value: 'My New Workflow' } });
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Save & Deploy Workflow'));
    });

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'My New Workflow',
        trigger_type: 'document_created',
      })
    );
  });

  it('WorkflowApprovalQueue renders pending approvals with Approve/Reject actions', () => {
    const mockApprovals: WorkflowApprovalItem[] = [
      {
        id: 'appr-1',
        execution_id: 'exec-12345678',
        workflow_name: 'Expense Reimbursement',
        step_name: 'Manager Gate',
        status: 'pending',
        created_at: '2026-10-28T12:00:00Z',
      },
    ];

    const onDecide = vi.fn();

    render(
      <WorkflowApprovalQueue
        approvals={mockApprovals}
        onDecide={onDecide}
        isLoading={false}
      />
    );

    expect(screen.getByText('Expense Reimbursement')).toBeDefined();
    expect(screen.getByText('Step: Manager Gate')).toBeDefined();
    expect(screen.getByText('Approve')).toBeDefined();
    expect(screen.getByText('Reject')).toBeDefined();
  });

  it('NotificationCenterDrawer displays notifications and filter options', () => {
    const mockNotifs = [
      {
        id: 'notif-1',
        organization_id: 'org-1',
        user_id: 'u-1',
        channel: 'in_app' as const,
        priority: 'high' as const,
        category: 'workflow' as const,
        title: 'Workflow Completed',
        content: 'Pipeline doc-index finished with 0 errors.',
        is_read: false,
        created_at: '2026-10-28T12:00:00Z',
      },
    ];

    const onClose = vi.fn();
    const onMarkRead = vi.fn();
    const onMarkAllRead = vi.fn();

    render(
      <NotificationCenterDrawer
        isOpen={true}
        onClose={onClose}
        notifications={mockNotifs}
        unreadCount={1}
        onMarkRead={onMarkRead}
        onMarkAllRead={onMarkAllRead}
      />
    );

    expect(screen.getByText('Notification Inbox')).toBeDefined();
    expect(screen.getByText('Workflow Completed')).toBeDefined();
    expect(screen.getByText('Pipeline doc-index finished with 0 errors.')).toBeDefined();

    fireEvent.click(screen.getByText('Mark read'));
    expect(onMarkRead).toHaveBeenCalledWith('notif-1');
  });

  it('WorkflowTemplateGallery renders blueprints with Deploy action', () => {
    const mockTemplates: WorkflowTemplateItem[] = [
      {
        id: 'tpl-1',
        name: 'Auto-Index On Upload',
        description: 'Automatically triggers embedding and KG entity extraction.',
        category: 'Ingestion',
        complexity: 'simple',
        is_built_in: true,
        trigger_type: 'document_created',
        condition_rules: [],
        steps_template: [
          {
            step_order: 1,
            name: 'Notify Team',
            action_type: 'send_notification',
            action_config: {},
          },
        ],
        created_at: '2026-10-28T00:00:00Z',
      },
    ];

    const onSelect = vi.fn();

    render(
      <WorkflowTemplateGallery
        templates={mockTemplates}
        onSelectTemplate={onSelect}
      />
    );

    expect(screen.getByText('Auto-Index On Upload')).toBeDefined();
    expect(screen.getByText('Deploy Template')).toBeDefined();

    fireEvent.click(screen.getByText('Deploy Template'));
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Auto-Index On Upload',
        trigger_type: 'document_created',
      })
    );
  });

  it('WorkflowAnalyticsDashboard displays metrics meters', () => {
    const mockAnalytics: WorkflowAnalyticsData = {
      total_workflows: 10,
      active_workflows: 8,
      total_executions: 250,
      successful_executions: 245,
      failed_executions: 5,
      success_rate: 98.0,
      average_duration_ms: 1450,
      pending_approvals_count: 1,
      executions_by_day: [],
    };

    render(<WorkflowAnalyticsDashboard analytics={mockAnalytics} />);

    expect(screen.getByText('Workflow Execution Analytics')).toBeDefined();
    expect(screen.getByText('98.0%')).toBeDefined();
    expect(screen.getByText('250')).toBeDefined();
    expect(screen.getByText('1.45s')).toBeDefined();
  });

  it('NotificationPreferencesModal renders channel matrix and triggers updates', async () => {
    const onClose = vi.fn();
    const onUpdate = vi.fn().mockResolvedValue({});
    const mockPrefs = [
      {
        category: 'workflow' as const,
        in_app: true,
        email: false,
        slack: false,
        teams: false,
      },
    ];

    render(
      <NotificationPreferencesModal
        isOpen={true}
        onClose={onClose}
        preferences={mockPrefs}
        onUpdatePreference={onUpdate}
      />
    );

    expect(screen.getByText('Notification Delivery Preferences')).toBeDefined();
    expect(screen.getByText('Workflow Automation')).toBeDefined();
    expect(screen.getByText('In-App')).toBeDefined();
    expect(screen.getByText('Email')).toBeDefined();

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThan(0);

    await act(async () => {
      fireEvent.click(checkboxes[0]);
    });

    expect(onUpdate).toHaveBeenCalled();
  });
});
