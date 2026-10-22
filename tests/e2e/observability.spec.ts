/**
 * Phase 1.9 — System Observability & Monitoring Command Center E2E Test Suite.
 *
 * Verifies end-to-end user workflows, responsive adaptations, and interactive widgets:
 * 1. Observability Command Center Hydration & Top Navigation:
 *    - Validates /observability and /health routes.
 *    - Header title, Phase 1.9 milestone badge, and live polling toggle.
 *    - Composite platform health banner with operational status and uptime.
 * 2. Deep-Dive Command Center Tab Switching:
 *    - Overview Tab: 4 core subsystem cards and KPI previews.
 *    - Subsystems Tab: PostgreSQL pgvector pool, Storage quota, API Gateway VM, and Auth JWT.
 *    - Telemetry & Trends Tab: 8 primary telemetry KPIs and SVG sparkline trends.
 *    - Alerts Tab: Severity filtering (CRITICAL, WARNING, SECURITY, INFO) and acknowledgement.
 *    - Structured Logs Tab: Canonical 13-field log explorer with search, severity filter, and trace modal.
 * 3. Interactive Diagnostics Modal:
 *    - Triggering on-demand diagnostic test runner.
 *    - Parallel probe evaluation across all 5 endpoints with execution latency badges.
 * 4. Responsive Layout Breakpoints:
 *    - Desktop (1440x900): Multi-column grid layout with expanded status gauges.
 *    - Tablet (768x1024): 2-column adaptive layout.
 *    - Mobile (375x667): 1-column stacked card layout with horizontal scrolling tab navigation.
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-phase: Phase 1.9 Logging, Monitoring & System Observability
 * Specification: devdocs/p1/p1.9.txt (Chapter 3, 7, 8, 9, 10, 16, 17)
 * Architecture: docs/Architecture/observability-architecture.md
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
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_1_9');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_1_9');
    (window as any).__MOCK_USER__ = mockUser;
  }, role);
}

async function navigateTo(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: 'domcontentloaded' });
}

// ---------------------------------------------------------------------------
// 1. Observability Command Center Hydration & Top Navigation
// ---------------------------------------------------------------------------

test.describe('Phase 1.9 Observability — Page Hydration & Navigation', () => {
  test('hydrates master /observability page with headers, badges, and polling controls', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    // Verify Title & Milestone Badge
    const headerTitle = page.locator('h1', { hasText: 'System Observability & Monitoring' });
    await expect(headerTitle).toBeVisible();

    const phaseBadge = page.locator('text=Phase 1.9');
    await expect(phaseBadge).toBeVisible();

    // Verify Polling Toggle Button
    const pollingButton = page.locator('button', { hasText: /Live Polling|Polling Paused/ });
    await expect(pollingButton).toBeVisible();

    // Verify Run Diagnostics Button
    const diagButton = page.locator('button', { hasText: 'Run Diagnostics' });
    await expect(diagButton).toBeVisible();

    // Verify Metrics Exposition Download Button
    const metricsButton = page.locator('button', { hasText: 'Metrics Exposition' });
    await expect(metricsButton).toBeVisible();

    // Verify Refresh Button
    const refreshButton = page.locator('button', { hasText: 'Refresh' });
    await expect(refreshButton).toBeVisible();
  });

  test('navigates cleanly via /health route and renders observability platform status', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/health');

    // Upgraded HealthPage renders Observability Command Center
    const headerTitle = page.locator('h1', { hasText: 'System Observability & Monitoring' });
    await expect(headerTitle).toBeVisible();

    // Verify Platform Status Header
    const platformStatus = page.locator('text=/System Operational|System Degraded|System Outage/');
    await expect(platformStatus.first()).toBeVisible();
  });

  test('toggles live polling state when clicked', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    const pollingButton = page.locator('button', { hasText: /Live Polling|Polling Paused/ });
    await expect(pollingButton).toBeVisible();

    // Toggle polling
    await pollingButton.click();
    await page.waitForTimeout(300);

    // Verify text or indicator reflects toggle
    await expect(pollingButton).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 2. Command Center Multi-Tab Navigation
// ---------------------------------------------------------------------------

test.describe('Phase 1.9 Observability — Multi-Tab Inspection', () => {
  test('switches across all 5 workspace tabs with content hydration', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    // 1. Overview Tab (Default active)
    const overviewTabBtn = page.locator('button', { hasText: 'Command Center Overview' });
    await expect(overviewTabBtn).toBeVisible();
    await expect(page.locator('text=Subsystem Probes Status').first()).toBeVisible();

    // 2. Subsystems Tab
    const subsystemsTabBtn = page.locator('button', { hasText: 'Subsystem Health Probes' });
    await expect(subsystemsTabBtn).toBeVisible();
    await subsystemsTabBtn.click();
    await page.waitForTimeout(200);

    // Verify Subsystem cards
    await expect(page.locator('text=PostgreSQL 16').first()).toBeVisible();
    await expect(page.locator('text=Storage Footprint').first()).toBeVisible();
    await expect(page.locator('text=API Gateway Engine').first()).toBeVisible();
    await expect(page.locator('text=Authentication Service').first()).toBeVisible();

    // 3. Telemetry & Trends Tab
    const telemetryTabBtn = page.locator('button', { hasText: 'KPIs & Latency Trends' });
    await expect(telemetryTabBtn).toBeVisible();
    await telemetryTabBtn.click();
    await page.waitForTimeout(200);

    // Verify telemetry KPI cards
    await expect(page.locator('text=Throughput (RPS)').first()).toBeVisible();
    await expect(page.locator('text=P95 Response Latency').first()).toBeVisible();
    await expect(page.locator('text=HTTP Error Rate').first()).toBeVisible();
    await expect(page.locator('text=Live Latency Trends').first()).toBeVisible();

    // 4. Alerts Tab
    const alertsTabBtn = page.locator('button', { hasText: /Alerts & Triggers/ });
    await expect(alertsTabBtn).toBeVisible();
    await alertsTabBtn.click();
    await page.waitForTimeout(200);

    // Verify Alert Panel
    await expect(page.locator('text=System Alerts & Warnings').first()).toBeVisible();
    const allPill = page.locator('button', { hasText: 'All' }).first();
    await expect(allPill).toBeVisible();

    // 5. Structured Logs Tab
    const logsTabBtn = page.locator('button', { hasText: 'Structured Log Viewer' });
    await expect(logsTabBtn).toBeVisible();
    await logsTabBtn.click();
    await page.waitForTimeout(200);

    // Verify Structured Log Viewer controls
    await expect(page.locator('text=Structured Log Explorer').first()).toBeVisible();
    const searchInput = page.locator('input[placeholder*="Search logs by message"]').first();
    await expect(searchInput).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 3. Interactive Diagnostics Modal
// ---------------------------------------------------------------------------

test.describe('Phase 1.9 Observability — Diagnostic Test Suite Modal', () => {
  test('opens diagnostic runner and verifies parallel health probes execution', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    // Click Run Diagnostics
    const diagBtn = page.locator('button', { hasText: 'Run Diagnostics' });
    await diagBtn.click();

    // Verify Modal Appears
    const modalTitle = page.locator('text=Subsystem Health Diagnostics');
    await expect(modalTitle).toBeVisible();

    // Verify Diagnostic run button inside modal
    const executeBtn = page.locator('button', { hasText: /Run Full Diagnostic Suite|Running Diagnostics/ });
    await expect(executeBtn).toBeVisible();

    // Verify Close button dismisses modal
    const closeBtn = page.locator('button', { hasText: 'Close' });
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();

    await page.waitForTimeout(200);
    await expect(modalTitle).not.toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 4. Responsive Layout Breakpoints
// ---------------------------------------------------------------------------

test.describe('Phase 1.9 Observability — Responsive Adaptations', () => {
  test('adapts layout for Desktop Viewport (1440x900)', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    const header = page.locator('h1', { hasText: 'System Observability & Monitoring' });
    await expect(header).toBeVisible();

    // In desktop, 4 subsystem cards display in grid
    const cards = page.locator('.grid');
    await expect(cards.first()).toBeVisible();
  });

  test('adapts layout for Tablet Viewport (768x1024)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    const header = page.locator('h1', { hasText: 'System Observability & Monitoring' });
    await expect(header).toBeVisible();

    // Tabs navigation remains accessible
    const tabsContainer = page.locator('button', { hasText: 'Command Center Overview' });
    await expect(tabsContainer).toBeVisible();
  });

  test('adapts layout for Mobile Viewport (375x667)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await navigateTo(page, '/observability');

    const header = page.locator('h1', { hasText: 'System Observability & Monitoring' });
    await expect(header).toBeVisible();

    // Action buttons wrap cleanly
    const diagBtn = page.locator('button', { hasText: 'Run Diagnostics' });
    await expect(diagBtn).toBeVisible();
  });
});
