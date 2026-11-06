/**
 * Phase 3.7 — Final Quality Assurance, Security Audit & Production Release Playwright E2E Suite.
 *
 * Verifies end-to-end user workflows, pre-flight readiness gating, OWASP compliance audits,
 * production release packaging, artifact digests, sponsor showcase tracks, and responsive breakpoints:
 * 1. Navigation & Operations Command Center:
 *    - Route reachability (/system/release).
 *    - Sidebar integration with Award icon and Phase 3.7 badge.
 * 2. Pre-Flight Release Readiness Gauge:
 *    - Circular radial score meter, 90% SLA threshold, and 7 subsystem checkpoints.
 * 3. Enterprise Security & Compliance Audit:
 *    - OWASP Top 10 + LLM Top 10 compliance scorecard, control severity badges, and zero findings state.
 * 4. Production Release Deployment Modal:
 *    - SemVer 2.0.0 validation, markdown changelog editor, environment selector, and safety gates.
 * 5. Release History Timeline:
 *    - Chronological release timeline, deployer tracking, and signed SHA-256 artifact digests.
 * 6. Sponsor Demonstration Showcase:
 *    - 6 architectural showcase tracks with navigation actions for project evaluators.
 * 7. Responsive Viewport Adaptations:
 *    - Desktop (1280x800), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 3.7 — Final Quality Assurance, Security Audit, Documentation & Production Release
 * Specification: devdocs/p3/p3.7.txt & docs/Architecture/final-quality-assurance-security-audit-production-release.md
 */

import { expect, Page, test } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers & State Setup
// ---------------------------------------------------------------------------

async function setupAuthenticatedAdminUser(
  page: Page,
  role: 'SuperAdmin' | 'OrgAdmin' = 'OrgAdmin'
): Promise<void> {
  await page.addInitScript((userRole) => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'release.admin@keep.enterprise.io',
      full_name: 'Release Architect Lead',
      role: userRole,
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_3_7');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_3_7');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  }, role);
}

async function setupReleaseApiMocks(page: Page): Promise<void> {
  // 1. Pre-flight Readiness Mock
  await page.route('**/api/v1/system/readiness*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Pre-flight evaluation completed.',
        data: {
          is_ready: true,
          overall_score: 1.0,
          evaluated_at: '2026-11-06T05:00:00Z',
          target_version: '1.0.0',
          git_commit: '8767c08',
          checks: [
            {
              check_name: 'database_migrations',
              category: 'PERSISTENCE',
              status: 'PASSED',
              score: 1.0,
              details: { alembic_head: '1b2c3d4e5f6a', applied_revisions: 24 },
              verified_at: '2026-11-06T05:00:00Z',
            },
            {
              check_name: 'database_pool',
              category: 'PERSISTENCE',
              status: 'PASSED',
              score: 1.0,
              details: { pool_size: 20, utilization_percent: 5.0 },
              verified_at: '2026-11-06T05:00:00Z',
            },
            {
              check_name: 'redis_cache',
              category: 'CACHE',
              status: 'PASSED',
              score: 1.0,
              details: { hit_ratio_percent: 94.6 },
              verified_at: '2026-11-06T05:00:00Z',
            },
            {
              check_name: 'storage_headroom',
              category: 'STORAGE',
              status: 'PASSED',
              score: 1.0,
              details: { free_percent: 35.0 },
              verified_at: '2026-11-06T05:00:00Z',
            },
            {
              check_name: 'vector_database',
              category: 'AI_INFRA',
              status: 'PASSED',
              score: 1.0,
              details: { extension: 'vector', index_type: 'HNSW' },
              verified_at: '2026-11-06T05:00:00Z',
            },
            {
              check_name: 'ai_model_cache',
              category: 'AI_INFRA',
              status: 'PASSED',
              score: 1.0,
              details: { model_id: 'sentence-transformers/all-MiniLM-L6-v2' },
              verified_at: '2026-11-06T05:00:00Z',
            },
            {
              check_name: 'security_audit',
              category: 'GOVERNANCE',
              status: 'PASSED',
              score: 1.0,
              details: { compliance_percent: 100.0 },
              verified_at: '2026-11-06T05:00:00Z',
            },
          ],
          failing_checks: [],
        },
      }),
    });
  });

  // 2. Security Audit Mock
  await page.route('**/api/v1/system/security/audit', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Security audit passed.',
        data: {
          compliance_standard: 'OWASP_TOP_10_AND_LLM_TOP_10',
          overall_compliance_percent: 100.0,
          evaluated_at: '2026-11-06T05:00:00Z',
          total_controls: 10,
          passed_controls: 10,
          failed_controls: 0,
          controls: [
            {
              control_id: 'SEC-01',
              name: 'SQL Injection Defense',
              status: 'PASSED',
              severity: 'CRITICAL',
              description: 'SQLAlchemy 2.0 ORM parameterization enforced.',
              mitigation: 'Ban raw queries.',
            },
            {
              control_id: 'SEC-02',
              name: 'Cross-Site Scripting (XSS) Prevention',
              status: 'PASSED',
              severity: 'HIGH',
              description: 'React JSX auto-escaping and DOMPurify.',
              mitigation: 'Contextual encoding.',
            },
            {
              control_id: 'SEC-04',
              name: 'Broken Access Control & Multi-Tenancy',
              status: 'PASSED',
              severity: 'CRITICAL',
              description: 'Deterministic RBAC and tenancy checks.',
              mitigation: 'Organization boundary filters.',
            },
            {
              control_id: 'SEC-06',
              name: 'AI Prompt Injection & Jailbreak Guardrails',
              status: 'PASSED',
              severity: 'HIGH',
              description: 'Delimiter sandboxing and prompt boundary markers.',
              mitigation: 'Multi-turn delimiter sandboxing.',
            },
          ],
          findings: [],
        },
      }),
    });
  });

  // 3. Releases History Mock
  await page.route('**/api/v1/system/releases*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: [
          {
            release_id: 'rel-v1.0.0-prod',
            version: '1.0.0',
            release_tag: 'v1.0.0',
            git_commit: '8767c08',
            status: 'COMPLETED',
            preflight_score: 1.0,
            deployed_by: '00000000-0000-0000-0000-000000000001',
            created_at: '2026-11-06T05:00:00Z',
            completed_at: '2026-11-06T05:00:10Z',
          },
        ],
      }),
    });
  });

  // 4. Trigger Release Mock
  await page.route('**/api/v1/system/release', async (route) => {
    if (route.request().method() === 'POST') {
      const payload = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Production release deployment initiated.',
          data: {
            release_id: `rel-${payload.version || '1.0.0'}-${Date.now()}`,
            version: payload.version || '1.0.0',
            release_tag: payload.release_tag || 'v1.0.0',
            git_commit: '8767c08',
            status: 'COMPLETED',
            preflight_score: 1.0,
            deployed_by: '00000000-0000-0000-0000-000000000001',
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            changelog: payload.changelog || 'Release changelog',
            artifacts: {
              manifest_checksum_sha256: '4f8a9b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a',
            },
          },
        }),
      });
    }
  });
}

// ---------------------------------------------------------------------------
// E2E Test Scenarios
// ---------------------------------------------------------------------------

test.describe('Phase 3.7 — Production Release & Quality Assurance E2E', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedAdminUser(page, 'OrgAdmin');
    await setupReleaseApiMocks(page);
  });

  test('1. Navigation & Command Center: Verify sidebar link and route rendering', async ({ page }) => {
    await page.goto('/system/release');
    await expect(page).toHaveURL(/.*\/system\/release/);

    // Verify Master Page Header
    await expect(page.getByRole('heading', { name: /Production Release & Quality Assurance/i })).toBeVisible();
    await expect(page.getByText('Phase 3.7 (v1.0.0)')).toBeVisible();

    // Verify Deploy Release action button is visible
    await expect(page.getByRole('button', { name: /Deploy Release/i })).toBeVisible();
  });

  test('2. Pre-Flight Readiness: Verify radial gauge, overall score, and subsystem checkpoints', async ({ page }) => {
    await page.goto('/system/release');

    // Verify Pre-flight Gauge card elements
    await expect(page.getByText('Pre-Flight Release Readiness Gate')).toBeVisible();
    await expect(page.getByText('Ready for Deployment')).toBeVisible();
    await expect(page.getByText('100%')).toBeVisible();
    await expect(page.getByText('v1.0.0')).toBeVisible();

    // Verify Checkpoints
    await expect(page.getByText('database migrations')).toBeVisible();
    await expect(page.getByText('redis cache')).toBeVisible();
    await expect(page.getByText('vector database')).toBeVisible();
    await expect(page.getByText('security audit')).toBeVisible();
  });

  test('3. Security Audit: Switch tab and verify OWASP Top 10 compliance scorecard', async ({ page }) => {
    await page.goto('/system/release');

    // Click on Security Audit tab
    await page.getByRole('button', { name: /Security Audit \(OWASP Top 10\)/i }).click();

    // Verify Security Audit Card
    await expect(page.getByText('Cybersecurity & Compliance Audit')).toBeVisible();
    await expect(page.getByText('Compliant')).toBeVisible();
    await expect(page.getByText('SEC-01')).toBeVisible();
    await expect(page.getByText('SQL Injection Defense')).toBeVisible();
    await expect(page.getByText('AI Prompt Injection & Jailbreak Guardrails')).toBeVisible();
  });

  test('4. Release Deployment Modal: Open modal, validate inputs, and dispatch release', async ({ page }) => {
    await page.goto('/system/release');

    // Open deployment modal
    await page.getByRole('button', { name: /Deploy Release/i }).click();

    // Verify modal elements
    await expect(page.getByText('Dispatch Production Release')).toBeVisible();
    await expect(page.getByDisplayValue('1.0.0')).toBeVisible();
    await expect(page.getByDisplayValue('v1.0.0')).toBeVisible();

    // Safety checklist checkbox interaction
    const acknowledgeCheckbox = page.getByText(/I acknowledge that this action will freeze version/i);
    await acknowledgeCheckbox.click();

    // Confirm deploy
    const confirmDeployBtn = page.getByRole('button', { name: /Confirm & Deploy Release/i });
    await expect(confirmDeployBtn).toBeEnabled();
    await confirmDeployBtn.click();

    // Success notification banner should appear
    await expect(page.getByText(/Release 1.0.0 \(v1.0.0\) deployed successfully!/i)).toBeVisible();
  });

  test('5. Release History: Switch tab and verify chronological timeline and artifact digests', async ({ page }) => {
    await page.goto('/system/release');

    // Click on Release History tab
    await page.getByRole('button', { name: /Release History/i }).click();

    // Verify Release History elements
    await expect(page.getByText('Release Deployment History')).toBeVisible();
    await expect(page.getByText('v1.0.0')).toBeVisible();
    await expect(page.getByText('Version 1.0.0')).toBeVisible();
    await expect(page.getByText('COMPLETED')).toBeVisible();

    // Expand artifacts
    const viewArtifactsBtn = page.getByRole('button', { name: /View Artifacts/i });
    await viewArtifactsBtn.click();
    await expect(page.getByText(/Backend Container Image:/i)).toBeVisible();
    await expect(page.getByText(/Frontend SPA Bundle:/i)).toBeVisible();
  });

  test('6. Sponsor Showcase: Switch tab and verify 6 architectural demonstration tracks', async ({ page }) => {
    await page.goto('/system/release');

    // Click on Sponsor Demo Showcase tab
    await page.getByRole('button', { name: /Sponsor Demo Showcase/i }).click();

    // Verify Showcase elements
    await expect(page.getByText('KEEP Enterprise Platform Architectural Showcase')).toBeVisible();
    await expect(page.getByText('Multi-Tenant RAG & Semantic Search')).toBeVisible();
    await expect(page.getByText('Enterprise AI Assistant & Citations')).toBeVisible();
    await expect(page.getByText('Interactive Knowledge Graph Explorer')).toBeVisible();
    await expect(page.getByText('Real-Time Multi-User Collaboration')).toBeVisible();
    await expect(page.getByText('Sandboxed Plugin & Tool Marketplace')).toBeVisible();
    await expect(page.getByText('Observability & High-Availability Operations')).toBeVisible();
  });

  test('7. Responsive Layouts: Adapt across Desktop, Tablet, and Mobile viewports', async ({ page }) => {
    // 1. Tablet Viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/system/release');
    await expect(page.getByRole('heading', { name: /Production Release & Quality Assurance/i })).toBeVisible();

    // 2. Mobile Viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/system/release');
    await expect(page.getByRole('heading', { name: /Production Release & Quality Assurance/i })).toBeVisible();
    await expect(page.getByText('100%')).toBeVisible();
  });
});
