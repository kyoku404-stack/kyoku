import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import {
  EvidenceProvenanceDrawer,
  ResearchLaunchForm,
  ResearchReportViewer,
  ResearchRunList,
} from '@/features/research';
import type { EvidenceItem, ResearchReport, ResearchRunRecord } from '@/types/research';

const SAMPLE_EVIDENCE: EvidenceItem[] = [
  {
    evidence_id: 'ev_01',
    source_id: 'doc_payments_postmortem',
    source_title: 'Payments Gateway v3.4 Incident Postmortem',
    passage: 'Payment gateway v3.4 retry storm caused 62% of Q4 billing complaints.',
    retrieval_reference: 'doc_payments_postmortem#chunk:1',
    relevance_score: 0.94,
    document_date: '2026-01-15',
    access_tier: 'read',
  },
];

const SAMPLE_REPORT: ResearchReport = {
  research_id: 'res_demo_01',
  question: 'Why did customer complaints increase last quarter?',
  scope: 'Support records',
  required_output: 'detailed_report',
  status: 'completed',
  summary: 'Detailed investigation across 4 internal sources.',
  findings: [
    {
      finding_id: 'f_01',
      claim: 'Payment gateway v3.4 retry storm drove 62% of billing complaints.',
      claim_type: 'factual',
      evidence_ids: ['ev_01'],
      confidence: 'high',
      limitations: ['Source dated 2026-01-15.'],
      has_contradiction: true,
    },
  ],
  evidence: SAMPLE_EVIDENCE,
  contradictions: [
    {
      topic: 'Q4 Complaint Root Cause',
      description: 'Engineering postmortem vs Support retrospective.',
      evidence_ids: ['ev_01'],
      source_dates: ['2026-01-05', '2026-01-15'],
    },
  ],
  unresolved_questions: ['Which enterprise segment saw the largest churn?'],
  follow_up_suggestions: ['Correlate release timestamps with ticket volume.'],
  warnings: ['Sanitized untrusted control directives from 1 retrieved passage(s).'],
  correction_attempts: 0,
  sources_retrieved: 5,
  sources_retained: 4,
};

const SAMPLE_RUN: ResearchRunRecord = {
  research_id: 'res_demo_01',
  tenant_id: 'org_1',
  requested_by: 'u_1',
  question: 'Why did customer complaints increase last quarter?',
  scope: 'Support records',
  required_output: 'detailed_report',
  max_sources: 12,
  status: 'completed',
  contradictions: SAMPLE_REPORT.contradictions,
  unresolved_questions: SAMPLE_REPORT.unresolved_questions,
  follow_up_suggestions: SAMPLE_REPORT.follow_up_suggestions,
  warnings: SAMPLE_REPORT.warnings,
  correction_attempts: 0,
  sources_retrieved: 5,
  sources_retained: 4,
  correlation_id: 'corr_1',
  created_at: '2026-11-18T10:00:00Z',
  updated_at: '2026-11-18T10:00:01Z',
};

describe('Phase 4.5 Research UI Components', () => {
  it('loads demo prompt and submits ResearchLaunchForm', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<ResearchLaunchForm isSubmitting={false} canInvoke={true} onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: /Load Q4 Complaints Demo/i }));
    fireEvent.click(screen.getByRole('button', { name: /Run Investigation/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        question: expect.stringContaining('customer complaints increase'),
        required_output: 'detailed_report',
        mode: 'sync',
      })
    );
  });

  it('filters runs via accessible tabs and triggers Inspect Report', () => {
    const onFilterChange = vi.fn();
    const onInspectReport = vi.fn();
    const onInspectEvidence = vi.fn();
    const onCancelRun = vi.fn();
    const onRefresh = vi.fn();

    render(
      <ResearchRunList
        runs={[SAMPLE_RUN]}
        statusFilter="all"
        selectedRunId={null}
        isLoading={false}
        canInvoke={true}
        onFilterChange={onFilterChange}
        onRefresh={onRefresh}
        onInspectReport={onInspectReport}
        onInspectEvidence={onInspectEvidence}
        onCancelRun={onCancelRun}
      />
    );

    fireEvent.click(screen.getByRole('tab', { name: 'Completed' }));
    expect(onFilterChange).toHaveBeenCalledWith('completed');

    fireEvent.click(screen.getByRole('button', { name: /Inspect Report/i }));
    expect(onInspectReport).toHaveBeenCalledWith('res_demo_01');
  });

  it('renders findings, contradictions, and invokes citation click callback', () => {
    const onCitationClick = vi.fn();
    const onOpenAllEvidence = vi.fn();

    render(
      <ResearchReportViewer
        report={SAMPLE_REPORT}
        isLoading={false}
        onCitationClick={onCitationClick}
        onOpenAllEvidence={onOpenAllEvidence}
      />
    );

    expect(screen.getByText(/Surfaced Contradictions/i)).toBeInTheDocument();
    expect(screen.getByText(/high confidence/i)).toBeInTheDocument();

    const citationButtons = screen.getAllByRole('button', { name: '[ev_01]' });
    fireEvent.click(citationButtons[0]);
    expect(onCitationClick).toHaveBeenCalledWith('res_demo_01', 'ev_01');
  });

  it('renders insufficient evidence state with clear banner', () => {
    render(
      <ResearchReportViewer
        report={{
          ...SAMPLE_REPORT,
          status: 'insufficient_evidence',
          findings: [],
          evidence: [],
          contradictions: [],
        }}
        isLoading={false}
        onCitationClick={vi.fn()}
        onOpenAllEvidence={vi.fn()}
      />
    );
    expect(screen.getByText(/Insufficient Authorized Evidence/i)).toBeInTheDocument();
  });

  it('displays provenance details and closes drawer on Escape or Close button', () => {
    const onClose = vi.fn();
    render(
      <EvidenceProvenanceDrawer
        isOpen={true}
        isLoading={false}
        evidenceItems={SAMPLE_EVIDENCE}
        redactedCount={1}
        highlightedEvidenceId="ev_01"
        onClose={onClose}
      />
    );

    expect(screen.getByRole('dialog', { name: 'Evidence Provenance Drawer' })).toBeInTheDocument();
    expect(screen.getByText(/Payments Gateway v3.4 Incident Postmortem/i)).toBeInTheDocument();
    expect(screen.getByText(/1 restricted source passage/i)).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Close Drawer' }));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
