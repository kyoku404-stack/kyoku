import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '@/services/api';
import { researchService } from '@/services/researchService';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('researchService (Phase 4.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts a research investigation with optional Idempotency-Key header', async () => {
    const mockResp = {
      data: {
        success: true,
        message: 'Done',
        data: {
          research_id: 'res_001',
          status: 'completed',
          question: 'Why did Q4 complaints rise?',
          required_output: 'detailed_report',
          max_sources: 12,
          correlation_id: 'corr_001',
          status_url: '/api/v1/research/res_001',
          report_url: '/api/v1/research/res_001/report',
          evidence_url: '/api/v1/research/res_001/evidence',
        },
      },
    };
    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResp);

    const result = await researchService.startResearch(
      { question: 'Why did Q4 complaints rise?', mode: 'sync' },
      'idem-key-1'
    );

    expect(apiClient.post).toHaveBeenCalledWith(
      '/research',
      { question: 'Why did Q4 complaints rise?', mode: 'sync' },
      { headers: { 'Idempotency-Key': 'idem-key-1' } }
    );
    expect(result.data.research_id).toBe('res_001');
  });

  it('lists research runs with status filter', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: { items: [], total: 0 } },
    });

    const res = await researchService.listRuns({ status: 'completed', limit: 25 });
    expect(apiClient.get).toHaveBeenCalledWith('/research', {
      params: { status: 'completed', limit: 25 },
    });
    expect(res.data.total).toBe(0);
  });

  it('retrieves run detail, report, evidence, and triggers cancellation', async () => {
    vi.mocked(apiClient.get)
      .mockResolvedValueOnce({ data: { success: true, message: 'OK', data: { run: {}, events: [] } } })
      .mockResolvedValueOnce({ data: { success: true, message: 'OK', data: { research_id: 'res_1' } } })
      .mockResolvedValueOnce({
        data: {
          success: true,
          message: 'OK',
          data: { research_id: 'res_1', items: [], total: 0, redacted_count: 1 },
        },
      });
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { success: true, message: 'Cancelled', data: { run: {}, events: [] } },
    });

    await researchService.getRun('res_1');
    await researchService.getReport('res_1');
    const ev = await researchService.getEvidence('res_1');
    await researchService.cancelRun('res_1');

    expect(apiClient.get).toHaveBeenNthCalledWith(1, '/research/res_1');
    expect(apiClient.get).toHaveBeenNthCalledWith(2, '/research/res_1/report');
    expect(apiClient.get).toHaveBeenNthCalledWith(3, '/research/res_1/evidence');
    expect(ev.data.redacted_count).toBe(1);
    expect(apiClient.post).toHaveBeenCalledWith('/research/res_1/cancel');
  });
});
