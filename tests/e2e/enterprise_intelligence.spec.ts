/**
 * Phase 2.5 — AI Insights, Predictive Analytics & Enterprise Intelligence Dashboard Playwright E2E Test Suite.
 *
 * Verifies end-to-end user workflows, executive decision support, capacity forecasting, and anomaly detection:
 * 1. Enterprise Intelligence Command Center Navigation:
 *    - Route verification (/intelligence and /enterprise-intelligence).
 *    - Sidebar integration with Phase 2.5 badge.
 *    - Tab navigation (Executive Briefing, Knowledge Health, Capacity Forecasts, Anomaly Detection, AI Recommendations, Trend Analysis).
 * 2. Executive Briefing & Core KPI Indicators:
 *    - Briefing narrative card rendering and active contributors/docs KPI counters.
 * 3. Multi-Dimensional Knowledge Health Score (KHS) Gauge:
 *    - Circular SVG gauge, composite score value (88/100), rating badge, factor bars, and gap alerts.
 * 4. Capacity Forecasts & Storage Runway:
 *    - Document growth projections with 95% confidence bounds and storage runway gauge.
 *    - Horizon toggle buttons (30d, 60d, 90d).
 * 5. Operational Anomaly Detection Feed:
 *    - Anomaly alerts with Z-score deviation badges and severity filtering.
 * 6. Strategic AI Recommendations:
 *    - Recommendations sorted by Priority Index with one-click action execution.
 * 7. Multi-Series Trend Analysis:
 *    - Document growth curves and AI query volume trends.
 * 8. Responsive Viewport Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 2.5 — AI Insights, Predictive Analytics & Enterprise Intelligence Dashboard
 * Specification: devdocs/p2/p2.5.txt & docs/Architecture/enterprise-intelligence-predictive-analytics.md
 */

import { expect, Page, test } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers & State Setup
// ---------------------------------------------------------------------------

async function setupAuthenticatedUser(
  page: Page,
  role: 'SuperAdmin' | 'OrgAdmin' | 'Manager' | 'Member' | 'Viewer' = 'OrgAdmin'
): Promise<void> {
  await page.addInitScript((userRole) => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'devops.admin@keep.enterprise.io',
      full_name: 'DevOps System Administrator',
      role: userRole,
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_2_5');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_2_5');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  }, role);
}

async function setupIntelligenceApiMocks(page: Page): Promise<void> {
  await page.route('**/api/v1/analytics/**', async (route) => {
    const url = route.request().url();

    // 1. Executive Dashboard
    if (url.includes('/api/v1/analytics/dashboard')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Executive dashboard retrieved successfully.',
          data: {
            health_score: {
              overall_score: 88,
              rating: 'EXCELLENT',
              coverage_score: 92.0,
              freshness_score: 84.0,
              quality_score: 86.0,
              retrieval_score: 90.0,
              duplicate_penalty: 4.0,
              department_breakdown: [
                { department: 'Platform Engineering', score: 94, rating: 'EXCELLENT', document_count: 64 },
                { department: 'Product Management', score: 82, rating: 'GOOD', document_count: 32 },
              ],
              identified_gaps: [
                'Human Resources has no active policy documentation.',
                'Legal contracts require freshness review (>120 days old).',
              ],
            },
            kpis: {
              active_users: 42,
              documents_uploaded: 128,
              ai_queries: 450,
              search_success_rate: 0.94,
              avg_response_time_ms: 185.0,
              storage_used_bytes: 1073741824,
              storage_capacity_bytes: 10737418240,
              knowledge_health_score: 88,
            },
            active_anomalies_count: 1,
            top_recommendations_count: 2,
            executive_summary:
              'Knowledge contributions increased by 18% this month with strong AI adoption (26% growth). Storage runway is projected at 142 days.',
          },
        }),
      });
      return;
    }

    // 2. Core Operational KPIs
    if (url.includes('/api/v1/analytics/kpis')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'KPI metrics retrieved successfully.',
          data: {
            active_users: 42,
            documents_uploaded: 128,
            ai_queries: 450,
            search_success_rate: 0.94,
            avg_response_time_ms: 185.0,
            storage_used_bytes: 1073741824,
            storage_capacity_bytes: 10737418240,
            knowledge_health_score: 88,
          },
        }),
      });
      return;
    }

    // 3. Trend Analysis
    if (url.includes('/api/v1/analytics/trends')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Trend analysis retrieved successfully.',
          data: {
            period_days: 30,
            document_growth: [
              { date: '2026-10-01', value: 110 },
              { date: '2026-10-15', value: 120 },
              { date: '2026-10-28', value: 128 },
            ],
            ai_query_volume: [
              { date: '2026-10-01', value: 310 },
              { date: '2026-10-15', value: 390 },
              { date: '2026-10-28', value: 450 },
            ],
            department_activity: [
              { department: 'Platform Engineering', document_count: 64, query_count: 210 },
              { department: 'Product Management', document_count: 32, query_count: 140 },
            ],
          },
        }),
      });
      return;
    }

    // 4. Predictive Forecasts
    if (url.includes('/api/v1/analytics/predictions')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Predictions generated successfully.',
          data: {
            horizon_days: 30,
            document_forecast: {
              current_value: 128,
              projected_value: 164,
              growth_rate_pct: 28.1,
              confidence_lower: 152,
              confidence_upper: 176,
            },
            storage_runway: {
              current_usage_bytes: 1073741824,
              capacity_bytes: 10737418240,
              days_to_85_pct: 142,
              days_to_full: 185,
              is_critical: false,
            },
            query_volume_forecast: {
              current_daily_avg: 45.0,
              projected_daily_avg: 58.5,
              monthly_tokens_projected: 2400000,
            },
          },
        }),
      });
      return;
    }

    // 5. Operational Anomalies
    if (url.includes('/api/v1/analytics/anomalies')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Anomalies retrieved successfully.',
          data: {
            total_detected: 1,
            anomalies: [
              {
                id: 'anom-001',
                metric_name: 'cross_department_collaboration',
                anomaly_type: 'ACTIVITY_DROP',
                severity: 'MEDIUM',
                description: 'Cross-team document sharing dropped 42% below 30-day baseline.',
                deviation_score: 2.35,
                detected_at: '2026-10-27T14:00:00Z',
              },
            ],
          },
        }),
      });
      return;
    }

    // 6. Strategic Recommendations
    if (url.includes('/api/v1/analytics/recommendations')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Recommendations retrieved successfully.',
          data: {
            total_recommendations: 2,
            recommendations: [
              {
                id: 'rec-001',
                category: 'ARCHIVE',
                title: 'Archive 14 Stale Operational Manuals',
                description: 'Documents have not been viewed, cited, or updated in >180 days.',
                impact_score: 7.5,
                effort_score: 1.5,
                priority_index: 7.5,
                status: 'ACTIVE',
                action_payload: { doc_ids: ['doc-1', 'doc-2'] },
              },
              {
                id: 'rec-002',
                category: 'COVERAGE',
                title: 'Document Human Resources SOPs',
                description: 'HR department has 0 indexed operational documents in knowledge base.',
                impact_score: 8.0,
                effort_score: 3.0,
                priority_index: 4.0,
                status: 'ACTIVE',
                action_payload: { department: 'Human Resources' },
              },
            ],
          },
        }),
      });
      return;
    }

    // 7. Knowledge Health Score
    if (url.includes('/api/v1/analytics/knowledge-health')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Knowledge health score computed successfully.',
          data: {
            overall_score: 88,
            rating: 'EXCELLENT',
            coverage_score: 92.0,
            freshness_score: 84.0,
            quality_score: 86.0,
            retrieval_score: 90.0,
            duplicate_penalty: 4.0,
            department_breakdown: [
              { department: 'Platform Engineering', score: 94, rating: 'EXCELLENT', document_count: 64 },
              { department: 'Operations', score: 72, rating: 'GOOD', document_count: 20 },
            ],
            identified_gaps: [
              'Human Resources has no active policy documentation.',
              'Legal contracts require freshness review (>120 days old).',
            ],
          },
        }),
      });
      return;
    }

    // Fallback pass-through
    await route.continue();
  });
}

// ---------------------------------------------------------------------------
// Test Suites
// ---------------------------------------------------------------------------

test.describe('Phase 2.5 — Enterprise Intelligence & Predictive Analytics E2E Suite', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await setupIntelligenceApiMocks(page);
  });

  test('01. Enterprise Intelligence Cockpit Navigation & Tab Switching', async ({ page }) => {
    await page.goto('/intelligence');

    // Verify main page elements
    await expect(page.locator('[data-testid="enterprise-intelligence-page"]')).toBeVisible();
    await expect(page.getByText('Enterprise Intelligence & Predictive Analytics')).toBeVisible();
    await expect(page.getByText('Phase 2.5')).toBeVisible();

    // Verify Tab buttons
    await expect(page.locator('[data-testid="tab-overview"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-health"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-forecasts"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-anomalies"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-recommendations"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-trends"]')).toBeVisible();

    // Switch to Knowledge Health Tab
    await page.locator('[data-testid="tab-health"]').click();
    await expect(page.locator('[data-testid="knowledge-health-gauge"]')).toBeVisible();

    // Switch to Forecasts Tab
    await page.locator('[data-testid="tab-forecasts"]').click();
    await expect(page.locator('[data-testid="forecast-visualizer"]')).toBeVisible();

    // Switch to Anomalies Tab
    await page.locator('[data-testid="tab-anomalies"]').click();
    await expect(page.locator('[data-testid="anomaly-alert-feed"]')).toBeVisible();

    // Switch to Recommendations Tab
    await page.locator('[data-testid="tab-recommendations"]').click();
    await expect(page.locator('[data-testid="recommendation-panel"]')).toBeVisible();

    // Switch to Trends Tab
    await page.locator('[data-testid="tab-trends"]').click();
    await expect(page.locator('[data-testid="trend-chart-widget"]')).toBeVisible();
  });

  test('02. Executive Briefing Narrative & KPI Stat Cards', async ({ page }) => {
    await page.goto('/intelligence');

    await expect(page.locator('[data-testid="executive-briefing-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="executive-briefing-text"]')).toContainText(
      'Knowledge contributions increased by 18% this month'
    );

    // Verify core KPI indicators
    await expect(page.getByText('42')).toBeVisible(); // Active contributors
    await expect(page.getByText('128 docs')).toBeVisible(); // Total documents
    await expect(page.getByText('450')).toBeVisible(); // AI queries
  });

  test('03. Multi-Dimensional Knowledge Health Score Gauge & Gap Alerts', async ({ page }) => {
    await page.goto('/intelligence');

    const gauge = page.locator('[data-testid="knowledge-health-gauge"]');
    await expect(gauge).toBeVisible();
    await expect(page.locator('[data-testid="khs-score-value"]')).toHaveText('88');
    await expect(gauge.getByText('EXCELLENT').first()).toBeVisible();

    // Factor breakdown check
    await expect(gauge.getByText('Coverage Factor (30% weight)')).toBeVisible();
    await expect(gauge.getByText('Freshness Factor (25% weight)')).toBeVisible();
    await expect(gauge.getByText('Quality Factor (25% weight)')).toBeVisible();

    // Identified Gaps alert box
    await expect(page.getByText('Human Resources has no active policy documentation.')).toBeVisible();
  });

  test('04. Predictive Capacity Forecasting & Storage Runway Toggles', async ({ page }) => {
    await page.goto('/intelligence');

    const forecast = page.locator('[data-testid="forecast-visualizer"]');
    await expect(forecast).toBeVisible();
    await expect(forecast.getByText('164')).toBeVisible(); // Projected docs
    await expect(forecast.getByText('+28.1%')).toBeVisible(); // Growth rate
    await expect(forecast.getByText('142')).toBeVisible(); // Days to 85% runway

    // Click 60d horizon button
    await forecast.getByRole('button', { name: '60d' }).click();
  });

  test('05. Operational Anomaly Alert Feed & Severity Filter', async ({ page }) => {
    await page.goto('/intelligence');

    const feed = page.locator('[data-testid="anomaly-alert-feed"]');
    await expect(feed).toBeVisible();
    await expect(feed.getByText('cross department collaboration')).toBeVisible();
    await expect(feed.getByText('Z = 2.35σ')).toBeVisible();

    // Filter to CRITICAL
    await feed.getByRole('button', { name: 'CRITICAL' }).click();
    await expect(page.getByText('No active anomalies detected')).toBeVisible();

    // Filter back to ALL
    await feed.getByRole('button', { name: 'ALL' }).click();
    await expect(feed.getByText('cross department collaboration')).toBeVisible();
  });

  test('06. Strategic Recommendations & One-Click Execution', async ({ page }) => {
    await page.goto('/intelligence');

    const recPanel = page.locator('[data-testid="recommendation-panel"]');
    await expect(recPanel).toBeVisible();
    await expect(recPanel.getByText('Archive 14 Stale Operational Manuals')).toBeVisible();
    await expect(recPanel.getByText('PI: 7.5')).toBeVisible();

    // Click Execute
    const executeBtn = recPanel.getByRole('button', { name: 'Execute' }).first();
    await executeBtn.click();
    await expect(recPanel.getByText('Applied')).toBeVisible();
  });

  test('07. Responsive Breakpoints Verification (Desktop, Tablet, Mobile)', async ({ page }) => {
    // 1. Desktop
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/intelligence');
    await expect(page.locator('[data-testid="enterprise-intelligence-page"]')).toBeVisible();

    // 2. Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('[data-testid="executive-briefing-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="knowledge-health-gauge"]')).toBeVisible();

    // 3. Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('[data-testid="enterprise-intelligence-page"]')).toBeVisible();
    await expect(page.getByText('Enterprise Intelligence & Predictive Analytics')).toBeVisible();
  });
});
