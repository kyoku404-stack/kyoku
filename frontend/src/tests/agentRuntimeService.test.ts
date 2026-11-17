/**
 * Phase 4.2 — Agent Runtime & Execution Engine API Client Service Tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { agentRuntimeService } from '@/services/agentRuntimeService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 4.2 Agent Runtime Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('listAgents() queries /agents with optional params', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'ok',
        data: {
          items: [{ agent_id: 'reference', name: 'Reference Agent', version: '1.0.0', enabled: true, description: 'Ref', capabilities: [] }],
          total: 1,
        },
      },
    });

    const res = await agentRuntimeService.listAgents({ capability: 'read' });
    expect(apiClient.get).toHaveBeenCalledWith('/agents', { params: { capability: 'read' } });
    expect(res.data.total).toBe(1);
    expect(res.data.items[0].agent_id).toBe('reference');
  });

  it('submitExecution() posts to /agents/{agent_id}/executions with Idempotency-Key header', async () => {
    const payload = { goal: 'Summarize Q4 risk', input: { topic: 'risk' }, mode: 'async' as const };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Accepted',
        data: { execution_id: 'exec-1', agent_id: 'research-graph', status: 'QUEUED' },
      },
    });

    const res = await agentRuntimeService.submitExecution('research-graph', payload, 'idem-001');
    expect(apiClient.post).toHaveBeenCalledWith(
      '/agents/research-graph/executions',
      payload,
      { headers: { 'Idempotency-Key': 'idem-001' } }
    );
    expect(res.data.execution_id).toBe('exec-1');
  });

  it('listExecutions() queries /executions with status filter', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'ok', data: { items: [], total: 0 } },
    });

    const res = await agentRuntimeService.listExecutions({ status: 'SUCCEEDED', limit: 25 });
    expect(apiClient.get).toHaveBeenCalledWith('/executions', {
      params: { status: 'SUCCEEDED', limit: 25 },
    });
    expect(res.data.total).toBe(0);
  });

  it('getExecution() and getExecutionResult() query execution status and result endpoints', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        data: { success: true, message: 'ok', data: { execution_id: 'exec-2', status: 'SUCCEEDED' } },
      })
      .mockResolvedValueOnce({
        data: {
          success: true,
          message: 'ok',
          data: {
            execution_id: 'exec-2',
            agent_id: 'research-graph',
            execution_status: 'SUCCEEDED',
            status: 'succeeded',
            output: { summary: 'Done' },
            evidence: [{ source_id: 'doc-1', source_type: 'document' }],
            warnings: [],
            schema_version: '1.0',
          },
        },
      });

    const statusRes = await agentRuntimeService.getExecution('exec-2');
    const resultRes = await agentRuntimeService.getExecutionResult('exec-2');
    expect(apiClient.get).toHaveBeenNthCalledWith(1, '/executions/exec-2');
    expect(apiClient.get).toHaveBeenNthCalledWith(2, '/executions/exec-2/result');
    expect(statusRes.data.status).toBe('SUCCEEDED');
    expect(resultRes.data.evidence).toHaveLength(1);
  });

  it('cancelExecution() and retryExecution() post to /cancel and /retry endpoints', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        data: { success: true, message: 'Cancelled', data: { execution_id: 'exec-3', status: 'CANCELLED' } },
      })
      .mockResolvedValueOnce({
        data: { success: true, message: 'Retried', data: { execution_id: 'exec-4', attempt_number: 2 } },
      });

    const cancelRes = await agentRuntimeService.cancelExecution('exec-3');
    const retryRes = await agentRuntimeService.retryExecution('exec-3', { mode: 'sync' });

    expect(apiClient.post).toHaveBeenNthCalledWith(1, '/executions/exec-3/cancel');
    expect(apiClient.post).toHaveBeenNthCalledWith(2, '/executions/exec-3/retry', { mode: 'sync' });
    expect(cancelRes.data.status).toBe('CANCELLED');
    expect(retryRes.data.attempt_number).toBe(2);
  });

  it('getMetrics() queries /executions/metrics', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'ok',
        data: {
          total_completed: 12,
          active_executions: 1,
          success_rate_percent: 91.7,
          avg_duration_ms: 42.5,
          p95_duration_ms: 120,
          avg_queue_wait_ms: 4,
          timeout_count: 1,
          cancellation_count: 0,
          retry_count: 2,
          output_validation_failures: 0,
          executions_by_status: { SUCCEEDED: 11, TIMED_OUT: 1 },
          recent_events: [],
        },
      },
    });

    const res = await agentRuntimeService.getMetrics();
    expect(apiClient.get).toHaveBeenCalledWith('/executions/metrics');
    expect(res.data.total_completed).toBe(12);
    expect(res.data.success_rate_percent).toBe(91.7);
  });
});
