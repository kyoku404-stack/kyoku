import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '@/services/api';
import { autonomousWorkflowService } from '@/services/autonomousWorkflowService';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('autonomousWorkflowService (Phase 4.9)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts an autonomous workflow via relative /autonomous-workflows path', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        data: { execution_id: 'auto_wf_1', status: 'completed' },
      },
    });

    const payload = {
      objective: 'Investigate Q4 customer churn spike',
      workflow_id: 'churn_investigation',
      policy: { max_steps: 12, max_replans: 2, require_approval_for_writes: true },
    };

    const res = await autonomousWorkflowService.startWorkflow(payload);
    expect(apiClient.post).toHaveBeenCalledWith('/autonomous-workflows', payload);
    expect(res.data.execution_id).toBe('auto_wf_1');
  });

  it('lists workflows with status filter and fetches workflow, steps, and events', async () => {
    vi.mocked(apiClient.get)
      .mockResolvedValueOnce({ data: { success: true, data: [] } })
      .mockResolvedValueOnce({
        data: { success: true, data: { execution_id: 'auto_wf_1', status: 'completed' } },
      })
      .mockResolvedValueOnce({ data: { success: true, data: [] } })
      .mockResolvedValueOnce({
        data: { success: true, data: { execution_id: 'auto_wf_1', decisions: [], events: [] } },
      });

    await autonomousWorkflowService.listWorkflows({ status: 'completed', limit: 25 });
    await autonomousWorkflowService.getWorkflow('auto_wf_1');
    await autonomousWorkflowService.listSteps('auto_wf_1');
    await autonomousWorkflowService.getEvents('auto_wf_1');

    expect(apiClient.get).toHaveBeenNthCalledWith(1, '/autonomous-workflows', {
      params: { status: 'completed', limit: 25 },
    });
    expect(apiClient.get).toHaveBeenNthCalledWith(2, '/autonomous-workflows/auto_wf_1');
    expect(apiClient.get).toHaveBeenNthCalledWith(3, '/autonomous-workflows/auto_wf_1/steps');
    expect(apiClient.get).toHaveBeenNthCalledWith(4, '/autonomous-workflows/auto_wf_1/events');
  });

  it('resumes and cancels autonomous workflows', async () => {
    vi.mocked(apiClient.post)
      .mockResolvedValueOnce({
        data: { success: true, data: { execution_id: 'auto_wf_2', status: 'completed' } },
      })
      .mockResolvedValueOnce({
        data: { success: true, data: { execution_id: 'auto_wf_3', status: 'cancelled' } },
      });

    await autonomousWorkflowService.resumeWorkflow('auto_wf_2', {
      approve: true,
      reason: 'Approved',
    });
    await autonomousWorkflowService.cancelWorkflow('auto_wf_3', { reason: 'Aborted' });

    expect(apiClient.post).toHaveBeenNthCalledWith(1, '/autonomous-workflows/auto_wf_2/resume', {
      approve: true,
      reason: 'Approved',
    });
    expect(apiClient.post).toHaveBeenNthCalledWith(2, '/autonomous-workflows/auto_wf_3/cancel', {
      reason: 'Aborted',
    });
  });
});
