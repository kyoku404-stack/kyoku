/**
 * Phase 4.2 — Agent Runtime & Execution Engine Component Unit Tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import {
  ExecuteAgentModal,
  ExecutionListTable,
  ExecutionResultDrawer,
  RuntimeMetricsBanner,
} from '@/features/agents';
import type {
  ExecutionRecordItem,
  ExecutionResultData,
  RegisteredAgentItem,
  RuntimeMetricsData,
} from '@/types/agentRuntime';

const MOCK_AGENTS: RegisteredAgentItem[] = [
  {
    agent_id: 'research-graph',
    name: 'KEEP Research Graph Agent',
    version: '1.0.0',
    description: '2-step deterministic LangGraph research workflow',
    enabled: true,
    capabilities: [{ name: 'research', description: 'Research synthesis', access_tier: 'read' }],
  },
];

const MOCK_METRICS: RuntimeMetricsData = {
  total_completed: 24,
  active_executions: 2,
  executions_by_status: { SUCCEEDED: 22, FAILED: 1, TIMED_OUT: 1 },
  success_rate_percent: 91.7,
  avg_duration_ms: 185,
  p95_duration_ms: 420,
  avg_queue_wait_ms: 12,
  timeout_count: 1,
  cancellation_count: 2,
  retry_count: 3,
  output_validation_failures: 0,
  recent_events: [],
};

const MOCK_EXECUTIONS: ExecutionRecordItem[] = [
  {
    execution_id: 'exec-succeeded-001',
    task_id: 'task-1',
    agent_id: 'research-graph',
    agent_version: '1.0.0',
    tenant_id: 'org-1',
    requested_by: 'user-1',
    status: 'SUCCEEDED',
    mode: 'sync',
    goal: 'Synthesize Q4 enterprise security posture',
    correlation_id: 'corr-1',
    attempt_number: 1,
    parent_execution_id: null,
    idempotency_key: 'idem-1',
    cancel_requested: false,
    error_code: null,
    error_message: null,
    created_at: '2026-11-18T00:00:00Z',
    started_at: '2026-11-18T00:00:00Z',
    completed_at: '2026-11-18T00:00:01Z',
    deadline_at: null,
    duration_ms: 142,
    queue_wait_ms: 4,
    status_url: '/api/v1/executions/exec-succeeded-001',
    result_url: '/api/v1/executions/exec-succeeded-001/result',
  },
  {
    execution_id: 'exec-running-002',
    task_id: 'task-2',
    agent_id: 'reference',
    agent_version: '1.0.0',
    tenant_id: 'org-1',
    requested_by: 'user-1',
    status: 'RUNNING',
    mode: 'async',
    goal: 'Long-running audit synthesis',
    correlation_id: 'corr-2',
    attempt_number: 1,
    parent_execution_id: null,
    idempotency_key: null,
    cancel_requested: false,
    error_code: null,
    error_message: null,
    created_at: '2026-11-18T00:01:00Z',
    started_at: '2026-11-18T00:01:00Z',
    completed_at: null,
    deadline_at: null,
    duration_ms: null,
    queue_wait_ms: 8,
    status_url: '/api/v1/executions/exec-running-002',
    result_url: '/api/v1/executions/exec-running-002/result',
  },
  {
    execution_id: 'exec-failed-003',
    task_id: 'task-3',
    agent_id: 'research-graph',
    agent_version: '1.0.0',
    tenant_id: 'org-1',
    requested_by: 'user-1',
    status: 'FAILED',
    mode: 'async',
    goal: 'Transient upstream failure test',
    correlation_id: 'corr-3',
    attempt_number: 1,
    parent_execution_id: null,
    idempotency_key: null,
    cancel_requested: false,
    error_code: 'AGENT_TRANSIENT_FAILURE',
    error_message: 'Temporary upstream timeout',
    created_at: '2026-11-18T00:02:00Z',
    started_at: '2026-11-18T00:02:00Z',
    completed_at: '2026-11-18T00:02:02Z',
    deadline_at: null,
    duration_ms: 210,
    queue_wait_ms: 3,
    status_url: '/api/v1/executions/exec-failed-003',
    result_url: '/api/v1/executions/exec-failed-003/result',
  },
];

describe('Phase 4.2 Agent Runtime UI Components', () => {
  it('RuntimeMetricsBanner renders all 6 live KPI cards', () => {
    render(<RuntimeMetricsBanner metrics={MOCK_METRICS} />);
    expect(screen.getByText('Completed Runs')).toBeInTheDocument();
    expect(screen.getByText('24')).toBeInTheDocument();
    expect(screen.getByText('91.7%')).toBeInTheDocument();
    expect(screen.getByText('185 ms')).toBeInTheDocument();
    expect(screen.getByText('1 / 2')).toBeInTheDocument();
    expect(screen.getByText('Retries Scheduled')).toBeInTheDocument();
  });

  it('ExecuteAgentModal validates required goal, invalid JSON, and submits valid payload', async () => {
    const onSubmit = vi.fn().mockResolvedValue({ execution_id: 'exec-new' });
    const onClose = vi.fn();

    render(
      <ExecuteAgentModal
        isOpen={true}
        agents={MOCK_AGENTS}
        initialAgentId="research-graph"
        onClose={onClose}
        onSubmit={onSubmit}
      />
    );

    // Submitting with empty goal displays validation error
    fireEvent.click(screen.getByRole('button', { name: /Execute Agent/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/Execution goal is required/i);

    // Invalid JSON displays validation error
    fireEvent.change(screen.getByLabelText(/Execution Goal/i), {
      target: { value: 'Verify compliance report' },
    });
    fireEvent.change(screen.getByLabelText(/Structured Input Payload/i), {
      target: { value: '{invalid json' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Execute Agent/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/valid JSON/i);

    // Valid submission calls onSubmit with parsed input and Idempotency-Key
    fireEvent.change(screen.getByLabelText(/Structured Input Payload/i), {
      target: { value: '{"topic":"SOC2"}' },
    });
    fireEvent.change(screen.getByLabelText(/Idempotency Key/i), {
      target: { value: 'key-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Execute Agent/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        'research-graph',
        expect.objectContaining({
          goal: 'Verify compliance report',
          input: { topic: 'SOC2' },
          mode: 'sync',
        }),
        'key-123'
      );
    });
    expect(onClose).toHaveBeenCalled();
  });

  it('ExecutionListTable renders status filter tabs and contextual Inspect, Cancel, and Retry actions', () => {
    const onFilterChange = vi.fn();
    const onInspect = vi.fn();
    const onCancel = vi.fn();
    const onRetry = vi.fn();

    render(
      <ExecutionListTable
        executions={MOCK_EXECUTIONS}
        statusFilter="ALL"
        onFilterChange={onFilterChange}
        onInspect={onInspect}
        onCancel={onCancel}
        onRetry={onRetry}
      />
    );

    // Filter tab click
    fireEvent.click(screen.getByRole('tab', { name: 'Succeeded' }));
    expect(onFilterChange).toHaveBeenCalledWith('SUCCEEDED');

    // Inspect Result button on succeeded row
    fireEvent.click(screen.getAllByRole('button', { name: /Inspect Result/i })[0]);
    expect(onInspect).toHaveBeenCalledWith(MOCK_EXECUTIONS[0]);

    // Cancel button on running row
    fireEvent.click(screen.getByRole('button', { name: /^Cancel$/i }));
    expect(onCancel).toHaveBeenCalledWith('exec-running-002');

    // Retry button on failed row
    fireEvent.click(screen.getByRole('button', { name: /^Retry$/i }));
    expect(onRetry).toHaveBeenCalledWith('exec-failed-003');
  });

  it('ExecutionResultDrawer displays structured output, citations, warnings, and supports closing', () => {
    const onClose = vi.fn();
    const mockResult: ExecutionResultData = {
      execution_id: 'exec-succeeded-001',
      agent_id: 'research-graph',
      execution_status: 'SUCCEEDED',
      status: 'succeeded',
      output: { summary: 'All controls verified', steps_completed: 2 },
      evidence: [
        {
          source_id: 'doc-soc2-01',
          source_type: 'document',
          title: 'SOC2 Type II Report',
          excerpt: 'Zero critical findings across tenant isolation controls.',
        },
      ],
      warnings: ['Checkpoint state pruned older scratchpad fields'],
      error_code: null,
      error_message: null,
      error: null,
      schema_version: '1.0',
    };

    render(
      <ExecutionResultDrawer
        execution={MOCK_EXECUTIONS[0]}
        result={mockResult}
        onClose={onClose}
      />
    );

    expect(screen.getByText(/Execution Result & Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/All controls verified/i)).toBeInTheDocument();
    expect(screen.getByText('SOC2 Type II Report')).toBeInTheDocument();
    expect(screen.getByText(/Checkpoint state pruned/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Close Drawer' }));
    expect(onClose).toHaveBeenCalled();
  });
});
