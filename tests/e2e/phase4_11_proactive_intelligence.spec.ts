/**
 * Phase 4.11 — Proactive Enterprise Intelligence Playwright E2E Suite.
 */

import { expect, Page, test } from '@playwright/test';

async function setupAuthenticatedUser(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'intelligence.lead@keep.enterprise.io',
      full_name: 'Intelligence Lead',
      role: 'OrgAdmin',
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_4_11');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_4_11');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  });
}

async function setupIntelligenceApiMocks(page: Page): Promise<void> {
  const insights: Array<Record<string, unknown>> = [
    {
      insight_id: 'ins_e2e_001',
      tenant_id: '00000000-0000-0000-0000-000000000099',
      run_id: 'intel_run_e2e',
      category: 'significant_change',
      title: 'Material update detected in Retention Policy (v1 -> v2)',
      summary: 'Retention period updated from 90 days to 30 days.',
      observed_facts: ['Removed: 90 days', 'Added: 30 days'],
      inferred_explanation: 'May impact SOC2 compliance baseline.',
      limitations: [],
      evidence_refs: ['doc:pol-1:v1', 'doc:pol-1:v2'],
      evidence_records: [
        {
          evidence_id: 'evd_1',
          resource_ref: 'doc:pol-1:v1',
          source_type: 'document_version',
          validation_outcome: 'valid',
          snippet: 'Retain audit logs for 90 days.',
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
      dedup_key: 'dedup_e2e_1',
      detector_id: 'significant_change_detector',
      detector_version: '1.0.0',
      ranking_version: 'v1',
      workflow_execution_id: null,
      created_at: '2026-11-25T00:00:00Z',
      updated_at: '2026-11-25T00:00:00Z',
    },
  ];

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          id: '00000000-0000-0000-0000-000000000001',
          email: 'intelligence.lead@keep.enterprise.io',
          full_name: 'Intelligence Lead',
          role: 'OrgAdmin',
          organization_id: '00000000-0000-0000-0000-000000000099',
          is_active: true,
        },
      }),
    });
  });

  await page.route('**/api/v1/intelligence/metrics', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          tenant_id: '00000000-0000-0000-0000-000000000099',
          total_runs: 1,
          total_candidates: 1,
          published_insights: insights.filter((i) => i.status === 'published').length,
          suppressed_insights: 0,
          withheld_insights: 0,
          dismissed_insights: 0,
          resolved_insights: 0,
          duplicate_suppression_rate: 0,
          feedback_counts: {},
          category_counts: { significant_change: 1 },
        },
      }),
    });
  });

  await page.route('**/api/v1/intelligence/insights?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: insights }),
    });
  });

  await page.route('**/api/v1/intelligence/insights', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: insights }),
    });
  });

  await page.route('**/api/v1/intelligence/insights/ins_e2e_001', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: insights[0] }),
    });
  });

  await page.route('**/api/v1/intelligence/insights/ins_e2e_001/feedback', async (route) => {
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { feedback: 'useful' } }),
    });
  });

  await page.route('**/api/v1/intelligence/insights/ins_e2e_001/investigate', async (route) => {
    insights[0].status = 'investigating';
    insights[0].workflow_execution_id = 'wfexec_e2e_01';
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: insights[0] }),
    });
  });
}

test.describe('Phase 4.11 Proactive Enterprise Intelligence UI', () => {
  test('displays ranked insight feed, evidence, feedback, and workflow investigation', async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupIntelligenceApiMocks(page);

    await page.goto('/agents/intelligence');
    await expect(page.getByRole('heading', { name: 'Proactive Intelligence Feed' })).toBeVisible();
    await expect(page.getByText('doc:pol-1:v1')).toBeVisible();

    await page.getByRole('button', { name: 'Useful' }).click();
    await expect(page.getByRole('status')).toContainText("Feedback 'useful' recorded.");

    await page.getByRole('button', { name: 'Investigate Workflow' }).click();
    await expect(page.getByText('wfexec_e2e_01')).toBeVisible();
  });

  test('validates responsive layout on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await setupAuthenticatedUser(page);
    await setupIntelligenceApiMocks(page);

    await page.goto('/agents/intelligence');
    await expect(page.getByRole('heading', { name: 'Proactive Intelligence Feed' })).toBeVisible();
  });
});
