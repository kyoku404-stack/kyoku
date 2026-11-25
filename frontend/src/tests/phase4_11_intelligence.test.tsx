import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { IntelligenceFeedPage } from '@/pages/IntelligenceFeedPage';
import { proactiveIntelligenceService as intelligenceService } from '@/services/proactiveIntelligenceService';
import type { IntelligenceInsight, OperationalMetrics } from '@/types/proactiveIntelligence';

vi.mock('@/services/proactiveIntelligenceService', () => ({
  proactiveIntelligenceService: {
    listInsights: vi.fn(),
    getInsight: vi.fn(),
    getEvidence: vi.fn(),
    submitFeedback: vi.fn(),
    dismissInsight: vi.fn(),
    resolveInsight: vi.fn(),
    investigateInsight: vi.fn(),
    requestScan: vi.fn(),
    getMetrics: vi.fn(),
  },
}));

const SAMPLE_INSIGHT: IntelligenceInsight = {
  insight_id: 'ins_demo_001',
  tenant_id: 'org_1',
  run_id: 'intel_run_1',
  category: 'significant_change',
  title: 'Material update detected in Retention Policy (v1 -> v2)',
  summary: 'Audit log retention window shortened from 90 days to 30 days.',
  observed_facts: ['Removed: 90 days', 'Added: 30 days'],
  inferred_explanation: 'May conflict with SOC2 retention baseline.',
  limitations: ['Automated comparison; policy owner review advised.'],
  evidence_refs: ['doc:pol-1:v1', 'doc:pol-1:v2'],
  evidence_records: [
    {
      evidence_id: 'evd_1',
      resource_ref: 'doc:pol-1:v1',
      source_type: 'document_version',
      validation_outcome: 'valid',
      snippet: 'Audit logs must be retained for 90 days.',
      verified_at: '2026-11-25T00:00:00Z',
    },
  ],
  affected_resource_refs: ['doc:pol-1'],
  audience_roles: [],
  impact_score: 0.85,
  relevance_score: 0.82,
  evidence_quality_score: 0.92,
  urgency_score: 0.78,
  novelty_score: 0.88,
  priority_score: 85.6,
  confidence_score: 0.9,
  status: 'published',
  dedup_key: 'dedup_change_1',
  detector_id: 'significant_change_detector',
  detector_version: '1.0.0',
  ranking_version: 'v1',
  workflow_execution_id: null,
  created_at: '2026-11-25T00:00:00Z',
  updated_at: '2026-11-25T00:00:00Z',
};

const SAMPLE_METRICS: OperationalMetrics = {
  tenant_id: 'org_1',
  total_runs: 2,
  total_candidates: 2,
  published_insights: 1,
  suppressed_insights: 1,
  withheld_insights: 0,
  dismissed_insights: 0,
  resolved_insights: 0,
  duplicate_suppression_rate: 0.5,
  feedback_counts: { useful: 1 },
  category_counts: { significant_change: 1 },
};

describe('Phase 4.11 Proactive IntelligenceFeedPage', () => {
  it('renders metrics, ranked feed, evidence, and records feedback', async () => {
    vi.mocked(intelligenceService.listInsights).mockResolvedValue({
      success: true,
      data: [SAMPLE_INSIGHT],
    });
    vi.mocked(intelligenceService.getMetrics).mockResolvedValue({
      success: true,
      data: SAMPLE_METRICS,
    });
    vi.mocked(intelligenceService.getInsight).mockResolvedValue({
      success: true,
      data: SAMPLE_INSIGHT,
    });
    vi.mocked(intelligenceService.submitFeedback).mockResolvedValue({
      success: true,
      data: { feedback: 'useful' },
    });

    render(<IntelligenceFeedPage />);

    await waitFor(() => {
      expect(screen.getAllByText(/Material update detected/i).length).toBeGreaterThan(0);
    });

    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('doc:pol-1:v1')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Useful' }));
    await waitFor(() => {
      expect(intelligenceService.submitFeedback).toHaveBeenCalledWith('ins_demo_001', 'useful', undefined);
    });
    expect(screen.getByRole('status')).toHaveTextContent("Feedback 'useful' recorded.");
  });

  it('triggers manual proactive scan and workflow investigation', async () => {
    vi.mocked(intelligenceService.listInsights).mockResolvedValue({
      success: true,
      data: [SAMPLE_INSIGHT],
    });
    vi.mocked(intelligenceService.getMetrics).mockResolvedValue({
      success: true,
      data: SAMPLE_METRICS,
    });
    vi.mocked(intelligenceService.getInsight).mockResolvedValue({
      success: true,
      data: SAMPLE_INSIGHT,
    });
    vi.mocked(intelligenceService.requestScan).mockResolvedValue({
      success: true,
      data: {
        run_id: 'intel_run_2',
        tenant_id: 'org_1',
        trigger_source: 'manual',
        detector_versions: {},
        status: 'completed',
        candidates_generated: 1,
        insights_published: 1,
        insights_suppressed: 0,
        detector_errors: [],
        started_at: '2026-11-25T00:00:00Z',
      },
    });
    vi.mocked(intelligenceService.investigateInsight).mockResolvedValue({
      success: true,
      data: { ...SAMPLE_INSIGHT, status: 'investigating', workflow_execution_id: 'wfexec_99' },
    });

    render(<IntelligenceFeedPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Investigate Workflow' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Scan Policy Update' }));
    await waitFor(() => {
      expect(intelligenceService.requestScan).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Investigate Workflow' }));
    await waitFor(() => {
      expect(intelligenceService.investigateInsight).toHaveBeenCalledWith(
        'ins_demo_001',
        'knowledge_analysis'
      );
    });
  });
});
