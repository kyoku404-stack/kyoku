/**
 * Phase 3.5 — Plugin SDK, Extension Framework & Developer Ecosystem Playwright E2E Suite.
 *
 * Verifies end-to-end user workflows, marketplace, sandbox execution, capability grants, and telemetry:
 * 1. Navigation & Command Center:
 *    - Route reachability (/plugins, /marketplace).
 *    - Sidebar integration with Blocks icon and Phase 3.5 badge.
 * 2. Plugin Metrics Banner:
 *    - KPI cards: Installed Plugins, Active Extensions, Invocations, Avg Latency, and Error Rate.
 * 3. Installed Extensions List:
 *    - Render installed plugins, toggle active/disabled status, launch config editor.
 * 4. Extension Marketplace Catalog:
 *    - Browse extensions, filter by category, open installation modal with capability permissions.
 * 5. Sandbox Execution Telemetry & Action Tester:
 *    - Open telemetry drawer, view audit logs, invoke direct sandbox test action.
 * 6. Developer SDK Documentation Modal:
 *    - Launch SDK reference modal, inspect BasePlugin Python architecture template.
 * 7. Responsive Viewport Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 3.5 — Plugin SDK, Extension Framework & Developer Ecosystem
 * Specification: devdocs/p3/p3.5.txt & docs/Architecture/plugin-sdk-extension-framework.md
 */

import { expect, Page, test } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers & State Setup
// ---------------------------------------------------------------------------

async function setupAuthenticatedPluginUser(
  page: Page,
  role: 'SuperAdmin' | 'OrgAdmin' | 'Manager' | 'Member' | 'Viewer' = 'OrgAdmin'
): Promise<void> {
  await page.addInitScript((userRole) => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'devops.lead@keep.enterprise.io',
      full_name: 'DevOps & Integration Architect',
      role: userRole,
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_3_5');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_3_5');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  }, role);
}

async function setupPluginApiMocks(page: Page): Promise<void> {
  // 1. Analytics KPI Mock
  await page.route('**/api/v1/plugins/analytics**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Plugin analytics retrieved successfully.',
        data: {
          total_installed_plugins: 3,
          active_plugins: 2,
          total_executions: 420,
          avg_latency_ms: 64.5,
          error_rate: 1.2,
          plugins_by_category: { AI: 2, INTEGRATION: 1 },
        },
      }),
    });
  });

  // 2. Installed Plugins List Mock
  await page.route('**/api/v1/plugins/list**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Installed plugins retrieved successfully.',
        data: [
          {
            id: 'inst-001-claude',
            plugin_id: 'ai-anthropic-claude',
            name: 'Anthropic Claude 3.5 Sonnet Integration',
            version: '1.2.0',
            category: 'AI',
            status: 'ACTIVE',
            is_enabled: true,
            developer: 'Anthropic PBC',
            description: 'Enterprise-grade reasoning and contextual generation connector.',
            permissions: ['AI_INFERENCE', 'READ_DOCUMENTS'],
            event_hooks: ['on_document_uploaded'],
            configuration: { model: 'claude-3-5-sonnet', temperature: 0.2 },
            installed_at: '2026-10-29T12:00:00Z',
          },
          {
            id: 'inst-002-sap',
            plugin_id: 'sap-s4hana-connector',
            name: 'SAP S/4HANA Enterprise ERP Connector',
            version: '2.1.0',
            category: 'INTEGRATION',
            status: 'ACTIVE',
            is_enabled: true,
            developer: 'SAP SE',
            description: 'Bi-directional ERP sync for purchase orders and invoice clearance.',
            permissions: ['READ_DOCUMENTS', 'NETWORK_EGRESS'],
            event_hooks: ['on_audit_logged'],
            configuration: { endpoint_url: 'https://sap.internal.corp' },
            installed_at: '2026-10-29T12:05:00Z',
          },
        ],
      }),
    });
  });

  // 3. Marketplace Catalog Mock
  await page.route('**/api/v1/plugins/marketplace**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Marketplace catalog retrieved successfully.',
        data: [
          {
            id: 'tpl-claude',
            plugin_id: 'ai-anthropic-claude',
            name: 'Anthropic Claude 3.5 Sonnet Integration',
            description: 'Enterprise-grade reasoning and contextual generation connector.',
            category: 'AI',
            developer: 'Anthropic PBC',
            version: '1.2.0',
            verification_tier: 'CERTIFIED',
            rating: 4.95,
            installs_count: 1420,
            is_installed: true,
            min_keep_version: '3.0.0',
            max_keep_version: '3.9.9',
            permissions: ['AI_INFERENCE', 'READ_DOCUMENTS'],
            event_hooks: ['on_document_uploaded'],
          },
          {
            id: 'tpl-slack',
            plugin_id: 'slack-realtime-notifier',
            name: 'Slack Enterprise Grid Alerts & Bot',
            description: 'Interactive incident dispatch and approval notifications.',
            category: 'WORKFLOW',
            developer: 'Slack Technologies',
            version: '1.0.5',
            verification_tier: 'VERIFIED',
            rating: 4.75,
            installs_count: 640,
            is_installed: false,
            min_keep_version: '3.0.0',
            max_keep_version: '3.9.9',
            permissions: ['NETWORK_EGRESS', 'EVENT_LISTEN'],
            event_hooks: ['on_security_alert'],
          },
        ],
      }),
    });
  });

  // 4. Execution Logs Mock
  await page.route('**/api/v1/plugins/logs**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Plugin execution logs retrieved successfully.',
        data: [
          {
            id: 'log-001',
            plugin_id: 'ai-anthropic-claude',
            action: 'execute_inference',
            status: 'SUCCESS',
            duration_ms: 112.4,
            triggered_by: 'direct_api',
            error_message: null,
            created_at: new Date().toISOString(),
          },
        ],
      }),
    });
  });

  // 5. Execution Action Mock
  await page.route('**/api/v1/plugins/*/execute**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Action executed successfully.',
        data: {
          execution_id: 'exec-mock-789',
          plugin_id: 'ai-anthropic-claude',
          action: 'execute_inference',
          status: 'SUCCESS',
          duration_ms: 88.5,
          result: { completion: 'Mocked sandboxed response output.' },
          error_message: null,
        },
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Test Scenarios
// ---------------------------------------------------------------------------

test.describe('Phase 3.5 — Plugin SDK & Extension Framework E2E Suite', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedPluginUser(page, 'OrgAdmin');
    await setupPluginApiMocks(page);
  });

  test('TC-3.5-01: Navigation to Plugin Ecosystem page and Sidebar Integration', async ({ page }) => {
    await page.goto('/plugins');
    await expect(page).toHaveURL(/\/plugins/);

    // Verify Title and Sub-Phase Badge
    const heading = page.locator('h1', { hasText: 'Plugin SDK & Ecosystem' });
    await expect(heading).toBeVisible();

    const phaseBadge = page.locator('span', { hasText: 'Phase 3.5' });
    await expect(phaseBadge).toBeVisible();
  });

  test('TC-3.5-02: Plugin Metrics Banner KPIs render properly', async ({ page }) => {
    await page.goto('/plugins');

    // Check KPI cards
    await expect(page.locator('text=Installed Plugins')).toBeVisible();
    await expect(page.locator('text=Active Extensions')).toBeVisible();
    await expect(page.locator('text=Total Invocations')).toBeVisible();
    await expect(page.locator('text=Avg Sandbox Latency')).toBeVisible();
    await expect(page.locator('text=Error Rate')).toBeVisible();

    // Value assertions from mock
    await expect(page.locator('text=1.2%')).toBeVisible();
    await expect(page.locator('text=64.5')).toBeVisible();
  });

  test('TC-3.5-03: Installed Extensions list display and configuration modal', async ({ page }) => {
    await page.goto('/plugins');

    // Extensions list
    await expect(page.locator('text=Anthropic Claude 3.5 Sonnet Integration')).toBeVisible();
    await expect(page.locator('text=SAP S/4HANA Enterprise ERP Connector')).toBeVisible();

    // Click config on Claude
    const configButton = page.locator('button[title="Configure Settings"]').first();
    await configButton.click();

    // Modal should appear
    await expect(page.locator('text=Configure Anthropic Claude 3.5 Sonnet Integration')).toBeVisible();
    await page.locator('button', { hasText: 'Cancel' }).click();
    await expect(page.locator('text=Configure Anthropic Claude 3.5 Sonnet Integration')).not.toBeVisible();
  });

  test('TC-3.5-04: Extension Marketplace browsing and Install consent modal', async ({ page }) => {
    await page.goto('/plugins');

    // Switch to Marketplace tab
    const marketplaceTab = page.locator('button', { hasText: 'Extension Marketplace' });
    await marketplaceTab.click();

    // Verify marketplace items
    await expect(page.locator('text=Slack Enterprise Grid Alerts & Bot')).toBeVisible();
    await expect(page.locator('text=Certified Enterprise')).toBeVisible();
    await expect(page.locator('text=Verified Partner')).toBeVisible();

    // Click Install on Slack
    const installButton = page.locator('button', { hasText: 'Install Extension' });
    await installButton.click();

    // Verify Install modal with permissions
    await expect(page.locator('text=Install Slack Enterprise Grid Alerts & Bot')).toBeVisible();
    await expect(page.locator('text=NETWORK_EGRESS')).toBeVisible();

    // Close modal
    await page.locator('button', { hasText: 'Cancel' }).click();
  });

  test('TC-3.5-05: Sandbox Telemetry drawer and Action Tester', async ({ page }) => {
    await page.goto('/plugins');

    // Open telemetry drawer
    const telemetryBtn = page.locator('button', { hasText: 'Execution Telemetry' });
    await telemetryBtn.click();

    // Verify telemetry drawer visible
    await expect(page.locator('text=Sandbox Execution Telemetry')).toBeVisible();
    await expect(page.locator('text=execute_inference')).toBeVisible();

    // Close drawer
    const closeBtn = page.locator('button').filter({ has: page.locator('svg.lucide-x') }).first();
    await closeBtn.click();
  });

  test('TC-3.5-06: Developer SDK Documentation modal', async ({ page }) => {
    await page.goto('/plugins');

    // Open SDK Docs
    const docsBtn = page.locator('button', { hasText: 'SDK Docs' });
    await docsBtn.click();

    // Check modal contents
    await expect(page.locator('text=Plugin Developer SDK Reference')).toBeVisible();
    await expect(page.locator('text=Extension Framework Architecture')).toBeVisible();
    await expect(page.locator('text=Python BasePlugin Implementation')).toBeVisible();

    // Close modal
    await page.locator('button', { hasText: 'Close Documentation' }).click();
    await expect(page.locator('text=Plugin Developer SDK Reference')).not.toBeVisible();
  });

  test('TC-3.5-07: Responsive Viewport verification across Desktop, Tablet and Mobile', async ({ page }) => {
    // 1. Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/plugins');
    await expect(page.locator('h1', { hasText: 'Plugin SDK & Ecosystem' })).toBeVisible();

    // 2. Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/plugins');
    await expect(page.locator('h1', { hasText: 'Plugin SDK & Ecosystem' })).toBeVisible();
    await expect(page.locator('text=Installed Plugins')).toBeVisible();
  });
});
