/**
 * Phase 2.3 Assistant Service Unit Tests.
 * Verifies all 7 REST API methods in assistantService.
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { assistantService } from '@/services/assistantService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 2.3 Assistant Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('chat() sends conversational prompt and returns AssistantChatResponseData', async () => {
    const mockReply = {
      data: {
        success: true,
        message: 'Assistant message processed successfully.',
        data: {
          session_id: 'sess-123',
          message_id: 'm-456',
          reply: 'I found 3 relevant documents.',
          detected_intent: 'KNOWLEDGE_QA',
          workflow_id: 'wf-789',
          tools_executed: ['SearchTool'],
          requires_approval: false,
          created_at: new Date().toISOString(),
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockReply);

    const res = await assistantService.chat({ message: 'What is our travel policy?' });
    expect(apiClient.post).toHaveBeenCalledWith('/assistant/chat', {
      message: 'What is our travel policy?',
    });
    expect(res.data.detected_intent).toBe('KNOWLEDGE_QA');
    expect(res.data.reply).toBe('I found 3 relevant documents.');
  });

  it('executeTask() sends task instruction and returns TaskExecuteResponseData', async () => {
    const mockTask = {
      data: {
        success: true,
        message: 'Task plan formulated and execution initiated.',
        data: {
          workflow_id: 'wf-999',
          title: 'Document Rollup',
          status: 'COMPLETED',
          total_steps: 2,
          completed_steps: 2,
          steps: [
            {
              step_number: 1,
              tool_name: 'DocumentTool',
              description: 'Fetch files',
              status: 'COMPLETED',
              latency_ms: 45.2,
            },
          ],
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockTask);

    const res = await assistantService.executeTask({ instructions: 'Roll up documents' });
    expect(apiClient.post).toHaveBeenCalledWith('/assistant/task', {
      instructions: 'Roll up documents',
    });
    expect(res.data.workflow_id).toBe('wf-999');
    expect(res.data.completed_steps).toBe(2);
  });

  it('getHistory() queries conversation history sessions', async () => {
    const mockHistory = {
      data: {
        success: true,
        data: {
          sessions: [{ session_id: 's1', title: 'Session 1', message_count: 2, messages: [] }],
          total: 1,
          page: 1,
          page_size: 20,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockHistory);

    const res = await assistantService.getHistory();
    expect(apiClient.get).toHaveBeenCalledWith('/assistant/history', {
      params: { session_id: undefined, page: 1, page_size: 20 },
    });
    expect(res.data.sessions.length).toBe(1);
  });

  it('generateReport() posts report request and returns ReportGenerateResponseData', async () => {
    const mockReport = {
      data: {
        success: true,
        message: 'Report generated successfully.',
        data: {
          report_id: 'rep-1',
          report_type: 'WEEKLY_ROLLUP',
          title: 'Weekly Report',
          format: 'MARKDOWN',
          content: '# Weekly Report\nContent',
          created_at: new Date().toISOString(),
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockReport);

    const res = await assistantService.generateReport({
      report_type: 'WEEKLY_ROLLUP',
      title: 'Weekly Report',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/assistant/report', {
      report_type: 'WEEKLY_ROLLUP',
      title: 'Weekly Report',
    });
    expect(res.data.report_type).toBe('WEEKLY_ROLLUP');
  });

  it('getWorkflows() queries workflow execution progress', async () => {
    const mockWorkflows = {
      data: {
        success: true,
        data: {
          workflows: [
            {
              id: 'wf-1',
              title: 'Audit',
              trigger_type: 'CHAT',
              status: 'COMPLETED',
              total_steps: 3,
              completed_steps: 3,
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockWorkflows);

    const res = await assistantService.getWorkflows();
    expect(apiClient.get).toHaveBeenCalledWith('/assistant/workflows', {
      params: { status: undefined, page: 1, page_size: 20 },
    });
    expect(res.data.workflows.length).toBe(1);
  });

  it('processApproval() sends approval decision', async () => {
    const mockApproval = {
      data: {
        success: true,
        message: 'Approval processed successfully.',
        data: {
          approval_id: 'appr-1',
          decision: 'APPROVED',
          status: 'COMPLETED',
          executed_at: new Date().toISOString(),
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockApproval);

    const res = await assistantService.processApproval({
      approval_id: 'appr-1',
      decision: 'APPROVED',
      reason: 'Confirmed',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/assistant/approve', {
      approval_id: 'appr-1',
      decision: 'APPROVED',
      reason: 'Confirmed',
    });
    expect(res.data.decision).toBe('APPROVED');
  });

  it('getRecommendations() retrieves proactive enterprise recommendations', async () => {
    const mockRecs = {
      data: {
        success: true,
        data: {
          recommendations: [
            {
              id: 'rec-1',
              category: 'FREQUENT_DOCUMENTS',
              title: 'Handbook',
              description: 'Popular doc',
              suggested_action: 'Pin doc',
            },
          ],
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockRecs);

    const res = await assistantService.getRecommendations();
    expect(apiClient.get).toHaveBeenCalledWith('/assistant/recommendations');
    expect(res.data.recommendations.length).toBe(1);
  });
});
