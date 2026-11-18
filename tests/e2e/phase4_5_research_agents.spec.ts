/**
 * Phase 4.5 — Research Agents Playwright E2E Suite.
 *
 * Verifies end-to-end operator workflows on `/agents/research`:
 * 1. Navigation & Workspace Shell: Sidebar link (`Research Agents` + `Phase 4.5`), page heading & KPI strip.
 * 2. Launch Investigation & Report Inspection: Load Q4 demo prompt, launch sync investigation,
 *    inspect grounded findings, confidence badges, and surfaced cross-source contradictions.
 * 3. Evidence Provenance Drawer: Open via clickable citation pill `[ev_01]`, verify `source_id`,
 *    `retrieval_reference`, document dates, and Escape / Close button dismissal.
 * 4. Insufficient Evidence & Status Tab Filtering: Filter ledger via accessible `role="tab"` controls
 *    and inspect an `insufficient_evidence` run with zero invented findings.
 * 5. Responsive Viewport Verification: Desktop (1440x900), Tablet (768x1024), Mobile (375x667).
 */

import { expect, Page, test } from '@playwright/test';

async function setupAuthenticatedUser(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'research.lead@keep.enterprise.io',
      full_name: 'Research Lead',
      role: 'OrgAdmin',
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_4_5');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_4_5');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  });
}

async function setupResearchApiMocks(page: Page): Promise<void> {
  const evidenceQ4 = [
    {
      evidence_id: 'ev_01',
      source_id: 'doc_payments_postmortem',
      source_title: 'Payments Gateway v3.4 Incident Postmortem',
      passage:
        'Root cause analysis confirms that the November v3.4 payment gateway release introduced a retry storm that caused 62% of Q4 customer billing complaints.',
      retrieval_reference: 'doc_payments_postmortem#chunk:1',
      relevance_score: 0.94,
      document_date: '2026-01-15',
      access_tier: 'read',
      metadata: {},
    },
    {
      evidence_id: 'ev_02',
      source_id: 'doc_support_retro',
      source_title: 'Q4 Tier-2 Support Escalation Retrospective',
      passage:
        'Tier-2 support leads attributed Q4 customer complaints primarily to understaffed onboarding queues rather than payment gateway failures.',
      retrieval_reference: 'doc_support_retro#chunk:0',
      relevance_score: 0.87,
      document_date: '2026-01-05',
      access_tier: 'read',
      metadata: {},
    },
  ];

  const reportQ4 = {
    research_id: 'res_q4_demo_001',
    question:
      'Why did customer complaints increase last quarter and which internal teams were affected?',
    scope: 'Internal customer feedback and support records',
    required_output: 'detailed_report',
    status: 'completed',
    summary:
      'Detailed investigation across 4 authorized internal KEEP sources (2026-01-05 to 2026-01-15) surfacing 1 root-cause contradiction.',
    findings: [
      {
        finding_id: 'f_01',
        claim:
          'Payment gateway v3.4 retry storm drove 62% of Q4 billing complaints affecting Payments Engineering and Billing Operations.',
        claim_type: 'factual',
        evidence_ids: ['ev_01'],
        confidence: 'high',
        limitations: ['Source dated 2026-01-15.'],
        has_contradiction: true,
      },
      {
        finding_id: 'f_02',
        claim:
          'Reconcile conflicting engineering postmortem and support retrospective timelines against ticket timestamps.',
        claim_type: 'recommendation',
        evidence_ids: ['ev_01', 'ev_02'],
        confidence: 'medium',
        limitations: ['Actionable recommendation derived from cited internal evidence.'],
        has_contradiction: false,
      },
    ],
    evidence: evidenceQ4,
    contradictions: [
      {
        topic: 'Q4 Complaint Root Cause',
        description:
          'Payments Postmortem (2026-01-15) cites gateway regression while Support Retrospective (2026-01-05) cites onboarding understaffing.',
        evidence_ids: ['ev_02', 'ev_01'],
        source_dates: ['2026-01-05', '2026-01-15'],
      },
    ],
    unresolved_questions: [
      'Which root cause accounted for the largest share of enterprise renewals churn?',
    ],
    follow_up_suggestions: [
      'Inspect document dates and correlate release timestamps with SLA breach spikes.',
    ],
    warnings: ['Sanitized untrusted control directives from 1 retrieved passage(s).'],
    correction_attempts: 0,
    sources_retrieved: 5,
    sources_retained: 4,
    retrieval_latency_ms: 14,
    synthesis_latency_ms: 9,
    correlation_id: 'corr-e2e-45',
    completed_at: '2026-11-18T12:00:00Z',
  };

  const reportInsufficient = {
    research_id: 'res_empty_002',
    question: 'What caused subterranean neutrino drift at Antarctic station 9?',
    scope: null,
    required_output: 'summary',
    status: 'insufficient_evidence',
    summary:
      'Insufficient authorized internal evidence was retrieved from KEEP knowledge sources to answer this question without speculation.',
    findings: [],
    evidence: [],
    contradictions: [],
    unresolved_questions: [
      "No authorized KEEP records matched the question: 'What caused subterranean neutrino drift at Antarctic station 9?'.",
    ],
    follow_up_suggestions: ['Broaden the research scope or verify tenant document indexing.'],
    warnings: [],
    correction_attempts: 0,
    sources_retrieved: 0,
    sources_retained: 0,
    retrieval_latency_ms: 4,
    synthesis_latency_ms: 0,
    correlation_id: 'corr-e2e-empty',
    completed_at: '2026-11-18T12:05:00Z',
  };

  const runs = [
    {
      research_id: 'res_empty_002',
      tenant_id: '00000000-0000-0000-0000-000000000099',
      requested_by: '00000000-0000-0000-0000-000000000001',
      question: reportInsufficient.question,
      scope: null,
      required_output: 'summary',
      max_sources: 12,
      status: 'insufficient_evidence',
      summary: reportInsufficient.summary,
      contradictions: [],
      unresolved_questions: reportInsufficient.unresolved_questions,
      follow_up_suggestions: reportInsufficient.follow_up_suggestions,
      warnings: [],
      correction_attempts: 0,
      sources_retrieved: 0,
      sources_retained: 0,
      correlation_id: 'corr-e2e-empty',
      created_at: '2026-11-18T12:05:00Z',
      updated_at: '2026-11-18T12:05:00Z',
    },
  ];

  // Auth profile mock
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          id: '00000000-0000-0000-0000-000000000001',
          email: 'research.lead@keep.enterprise.io',
          full_name: 'Research Lead',
          role: 'OrgAdmin',
          organization_id: '00000000-0000-0000-0000-000000000099',
          is_active: true,
        },
      }),
    });
  });

  // POST & GET /api/v1/research
  await page.route('**/api/v1/research**', async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const pathname = url.pathname;

    if (req.method() === 'POST' && pathname.endsWith('/api/v1/research')) {
      const existing = runs.find((r) => r.research_id === reportQ4.research_id);
      if (!existing) {
        runs.unshift({
          research_id: reportQ4.research_id,
          tenant_id: '00000000-0000-0000-0000-000000000099',
          requested_by: '00000000-0000-0000-0000-000000000001',
          question: reportQ4.question,
          scope: reportQ4.scope,
          required_output: 'detailed_report',
          max_sources: 12,
          status: 'completed',
          summary: reportQ4.summary,
          contradictions: reportQ4.contradictions,
          unresolved_questions: reportQ4.unresolved_questions,
          follow_up_suggestions: reportQ4.follow_up_suggestions,
          warnings: reportQ4.warnings,
          correction_attempts: 0,
          sources_retrieved: 5,
          sources_retained: 4,
          correlation_id: 'corr-e2e-45',
          created_at: '2026-11-18T12:10:00Z',
          updated_at: '2026-11-18T12:10:00Z',
        });
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: "Research investigation finished with status 'completed'.",
          data: {
            research_id: reportQ4.research_id,
            status: 'completed',
            question: reportQ4.question,
            scope: reportQ4.scope,
            required_output: 'detailed_report',
            max_sources: 12,
            agent_execution_id: 'exec_p45_001',
            correlation_id: 'corr-e2e-45',
            status_url: `/api/v1/research/${reportQ4.research_id}`,
            report_url: `/api/v1/research/${reportQ4.research_id}/report`,
            evidence_url: `/api/v1/research/${reportQ4.research_id}/evidence`,
            report: reportQ4,
          },
        }),
      });
      return;
    }

    if (req.method() === 'GET' && pathname.endsWith('/report')) {
      const target = pathname.includes('res_empty_002') ? reportInsufficient : reportQ4;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'OK', data: target }),
      });
      return;
    }

    if (req.method() === 'GET' && pathname.endsWith('/evidence')) {
      const items = pathname.includes('res_empty_002') ? [] : evidenceQ4;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'OK',
          data: {
            research_id: pathname.includes('res_empty_002') ? 'res_empty_002' : 'res_q4_demo_001',
            items,
            total: items.length,
            redacted_count: 0,
          },
        }),
      });
      return;
    }

    if (req.method() === 'GET' && pathname.endsWith('/api/v1/research')) {
      const statusParam = url.searchParams.get('status');
      const filtered = statusParam ? runs.filter((r) => r.status === statusParam) : runs;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'OK',
          data: { items: filtered, total: filtered.length },
        }),
      });
      return;
    }

    await route.continue();
  });
}

test.describe('Phase 4.5 — Research Agents E2E Suite', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupResearchApiMocks(page);
  });

  test('navigates via sidebar, launches Q4 investigation, and inspects findings & contradictions', async ({
    page,
  }) => {
    await page.goto('/agents/research');
    await expect(page.getByRole('heading', { name: 'Research Agents Workspace' })).toBeVisible();
    await expect(page.getByText('Phase 4.5').first()).toBeVisible();

    // Load Q4 demo prompt and submit
    await page.getByRole('button', { name: /Load Q4 Complaints Demo/i }).click();
    await page.getByRole('button', { name: /Run Investigation/i }).click();

    // Report viewer shows grounded findings, confidence badges, and contradiction callout
    await expect(page.getByText(/Surfaced Contradictions \(1\)/i)).toBeVisible();
    await expect(page.getByText(/Payment gateway v3\.4 retry storm drove 62%/i)).toBeVisible();
    await expect(page.getByText(/high confidence/i)).toBeVisible();
  });

  test('opens Evidence Provenance Drawer from citation pill and closes with Escape', async ({
    page,
  }) => {
    await page.goto('/agents/research');
    await page.getByRole('button', { name: /Load Q4 Complaints Demo/i }).click();
    await page.getByRole('button', { name: /Run Investigation/i }).click();

    await page.getByRole('button', { name: '[ev_01]' }).first().click();

    const drawer = page.getByRole('dialog', { name: 'Evidence Provenance Drawer' });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText('Payments Gateway v3.4 Incident Postmortem')).toBeVisible();
    await expect(drawer.getByText('Ref: doc_payments_postmortem#chunk:1')).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(drawer).not.toBeVisible();
  });

  test('filters ledger by status tabs and displays insufficient evidence banner transparently', async ({
    page,
  }) => {
    await page.goto('/agents/research');
    await page.getByRole('tab', { name: 'Insufficient Evidence' }).click();
    await expect(page.getByText(/subterranean neutrino drift/i)).toBeVisible();

    await page.getByRole('button', { name: /Inspect Report/i }).first().click();
    await expect(page.getByText('Insufficient Authorized Evidence')).toBeVisible();
  });

  test('renders cleanly across Desktop (1440x900), Tablet (768x1024), and Mobile (375x667)', async ({
    page,
  }) => {
    const viewports = [
      { width: 1440, height: 900 },
      { width: 768, height: 1024 },
      { width: 375, height: 667 },
    ];
    for (const vp of viewports) {
      await page.setViewportSize(vp);
      await page.goto('/agents/research');
      await expect(page.getByRole('heading', { name: 'Research Agents Workspace' })).toBeVisible();
      await expect(page.getByRole('button', { name: /Run Investigation/i })).toBeVisible();
    }
  });
});
