/**
 * Phase 2.3 Assistant UI Components Test Suite.
 * Verifies rendering, interactions, accessibility, and state for:
 * - AssistantMetricsBanner
 * - WorkflowVisualizer
 * - ApprovalModal
 * - ReportViewer
 * - RecommendationsWidget
 * - AssistantChatBox
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  AssistantMetricsBanner,
  WorkflowVisualizer,
  ApprovalModal,
  ReportViewer,
  RecommendationsWidget,
  AssistantChatBox,
} from '@/features/assistant';
import type {
  AssistantMessage,
  AssistantMetrics,
  ProactiveRecommendationItem,
  ReportGenerateResponseData,
  TaskExecuteResponseData,
} from '@/types/assistant';

describe('Phase 2.3 Assistant UI Components', () => {
  describe('AssistantMetricsBanner', () => {
    const mockMetrics: AssistantMetrics = {
      active_workflows: 3,
      pending_approvals: 2,
      tasks_automated: 55,
      reports_generated: 12,
    };

    it('renders all 4 telemetry cards with correct values', () => {
      render(<AssistantMetricsBanner metrics={mockMetrics} />);
      expect(screen.getByText('Active Workflows')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('Pending Approvals')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('Automated Tasks')).toBeInTheDocument();
      expect(screen.getByText('55')).toBeInTheDocument();
      expect(screen.getByText('Reports Generated')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
    });
  });

  describe('WorkflowVisualizer', () => {
    it('renders empty placeholder when no active workflow is provided', () => {
      render(<WorkflowVisualizer workflow={null} />);
      expect(screen.getByText('No Active Workflow')).toBeInTheDocument();
    });

    it('renders DAG task pipeline nodes and status badges', () => {
      const mockWf: TaskExecuteResponseData = {
        workflow_id: 'wf-123',
        title: 'Quarterly Audit Pipeline',
        status: 'COMPLETED',
        total_steps: 2,
        completed_steps: 2,
        steps: [
          {
            step_number: 1,
            tool_name: 'DocumentTool',
            description: 'Fetch compliance files',
            status: 'COMPLETED',
            latency_ms: 120.4,
            output: { count: 3 },
          },
          {
            step_number: 2,
            tool_name: 'ReportTool',
            description: 'Generate report',
            status: 'COMPLETED',
            latency_ms: 210.1,
          },
        ],
        result_summary: '2 steps completed successfully.',
      };

      render(<WorkflowVisualizer workflow={mockWf} />);
      expect(screen.getByText('Quarterly Audit Pipeline')).toBeInTheDocument();
      expect(screen.getByText('DocumentTool')).toBeInTheDocument();
      expect(screen.getByText('ReportTool')).toBeInTheDocument();
      expect(screen.getByText('Progress: 2 of 2 steps finished')).toBeInTheDocument();
    });
  });

  describe('ApprovalModal', () => {
    const mockApproval = {
      approval_id: 'appr-abc',
      step_number: 1,
      action_type: 'UserTool',
      description: 'Remove user bob@corp.com from workspace',
      payload: { email: 'bob@corp.com', action: 'REMOVE' },
      status: 'PENDING',
    };

    it('renders approval dialog and triggers confirm decision', async () => {
      const onDecision = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(
        <ApprovalModal
          isOpen={true}
          onClose={onClose}
          approval={mockApproval}
          onDecision={onDecision}
        />
      );

      expect(screen.getByText('Human Approval Required')).toBeInTheDocument();
      expect(screen.getByText('Remove user bob@corp.com from workspace')).toBeInTheDocument();

      const confirmBtn = screen.getByText('Confirm & Execute');
      fireEvent.click(confirmBtn);

      expect(onDecision).toHaveBeenCalledWith('appr-abc', 'APPROVED', '');
    });

    it('triggers reject decision when Reject Action clicked', async () => {
      const onDecision = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(
        <ApprovalModal
          isOpen={true}
          onClose={onClose}
          approval={mockApproval}
          onDecision={onDecision}
        />
      );

      const rejectBtn = screen.getByText('Reject Action');
      fireEvent.click(rejectBtn);

      expect(onDecision).toHaveBeenCalledWith('appr-abc', 'REJECTED', '');
    });
  });

  describe('ReportViewer', () => {
    const mockReport: ReportGenerateResponseData = {
      report_id: 'rep-456',
      report_type: 'WEEKLY_ROLLUP',
      title: 'Weekly Executive Briefing',
      format: 'MARKDOWN',
      content: '# Weekly Executive Briefing\n\nAll metrics nominal.',
      created_at: new Date().toISOString(),
    };

    it('renders report preview with title and markdown content', () => {
      render(
        <ReportViewer
          isOpen={true}
          onClose={vi.fn()}
          report={mockReport}
          onGenerateReport={vi.fn()}
        />
      );

      expect(screen.getByText('Enterprise Report Generator')).toBeInTheDocument();
      expect(screen.getByText(/All metrics nominal/)).toBeInTheDocument();
      expect(screen.getByText('Copy Markdown')).toBeInTheDocument();
    });
  });

  describe('RecommendationsWidget', () => {
    const mockRecs: ProactiveRecommendationItem[] = [
      {
        id: 'r1',
        category: 'FREQUENT_DOCUMENTS',
        title: 'Employee Handbook 2026',
        description: 'Trending document with 45 queries this week.',
        suggested_action: 'Pin to workspace quick access',
      },
    ];

    it('renders recommendation card with suggested action and dismiss button', () => {
      const onDismiss = vi.fn();
      const onApply = vi.fn();

      render(
        <RecommendationsWidget
          recommendations={mockRecs}
          onDismiss={onDismiss}
          onApplyAction={onApply}
        />
      );

      expect(screen.getByText('Proactive AI Recommendations')).toBeInTheDocument();
      expect(screen.getByText('Employee Handbook 2026')).toBeInTheDocument();

      const actionBtn = screen.getByText(/Pin to workspace quick access/);
      fireEvent.click(actionBtn);
      expect(onApply).toHaveBeenCalledWith(mockRecs[0]);

      const dismissBtn = screen.getByTitle('Dismiss recommendation');
      fireEvent.click(dismissBtn);
      expect(onDismiss).toHaveBeenCalledWith('r1');
    });
  });

  describe('AssistantChatBox', () => {
    const mockMessages: AssistantMessage[] = [
      {
        id: 'm1',
        role: 'user',
        content: 'Summarize leave policies',
        created_at: new Date().toISOString(),
      },
      {
        id: 'm2',
        role: 'assistant',
        content: 'Leave policy entitles employees to 20 days paid leave.',
        intent: 'KNOWLEDGE_QA',
        tools_executed: ['SearchTool'],
        created_at: new Date().toISOString(),
      },
    ];

    it('renders conversational message stream with tool execution badge', () => {
      render(
        <AssistantChatBox
          messages={mockMessages}
          isLoading={false}
          onSendMessage={vi.fn()}
        />
      );

      expect(screen.getByText('Summarize leave policies')).toBeInTheDocument();
      expect(screen.getByText(/Leave policy entitles employees to 20 days paid leave/)).toBeInTheDocument();
      expect(screen.getByText('SearchTool')).toBeInTheDocument();
      expect(screen.getByText('KNOWLEDGE_QA')).toBeInTheDocument();
    });

    it('calls onSendMessage when submitting message text', () => {
      const onSend = vi.fn();
      render(
        <AssistantChatBox
          messages={mockMessages}
          isLoading={false}
          onSendMessage={onSend}
        />
      );

      const textarea = screen.getByPlaceholderText(/Ask a question, request a report/);
      fireEvent.change(textarea, { target: { value: 'Schedule a weekly rollup' } });

      const sendBtn = screen.getByTitle('Send Message');
      fireEvent.click(sendBtn);

      expect(onSend).toHaveBeenCalledWith('Schedule a weekly rollup');
    });
  });
});
