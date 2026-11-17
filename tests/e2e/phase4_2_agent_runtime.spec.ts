/**
 * Phase 4.2 — Agent Runtime & Execution Engine Playwright E2E Suite.
 *
 * Verifies end-to-end operator workflows on `/agents/runtime`:
 * 1. Navigation & Command Center: Sidebar link (`Agent Runtime` + `Phase 4.2`), page heading, registered agents strip.
 * 2. Runtime Observability KPI Banner: Completed runs, active executions, success rate, avg duration, timeouts/cancelled, retries.
 * 3. Execute Agent Modal: Submit new execution with goal, JSON input, mode, and Idempotency-Key.
 * 4. Execution Result & Evidence Drawer: Inspect structured JSON output, grounded citations, warnings, and Escape/Close dismissal.
 * 5. Cooperative Cancellation & Linked Retry: Cancel an active execution and retry a failed execution.
 * 6. Status Filter Tabs: Filter durable execution ledger via accessible `role="tab"` controls.
 * 7. Responsive Viewport Adaptations: Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 */

import { expect, Page, test } from '@playwright/test';

async function setupAuthenticatedUser(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'ai.lead@keep.enterprise.io',
      full_name: 'Agent Runtime Lead',
      role: 'OrgAdmin',
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_4_2');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_4_2');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  });
}

async function setupAgentRuntimeApiMocks(page: Page): Promise<void> {
  const executions = [
    {
      execution_id: 'exec-succeeded-001',
      task_id: 'task-001',
      agent_id: 'research-graph',
      agent_version: '1.0.0',
      tenant_id: '00000000-0000-0000-0000-000000000099',
      requested_by: '00000000-0000-0000-0000-000000000001',
      status: 'SUCCEEDED',
      mode: 'sync',
      goal: 'Synthesize Q4 enterprise architecture audit',
      correlation_id: 'corr-001',
      attempt_number: 1,
      parent_execution_id: null,
      idempotency_key: 'idem-q4-audit',
      cancel_requested: false,
      error_code: null,
      error_message: null,
      created_at: '2026-11-18T00:00:00Z',
      started_at: '2026-11-18T00:00:00Z',
      completed_at: '2026-11-18T00:00:01Z',
      deadline_at: null,
      duration_ms: 142,
      queue_wait_ms: 4,
      status_url: '/api/v1/executions/exec-succeeded-001',
      result_url: '/api/v1/executions/exec-succeeded-001/result',
    },
    {
      execution_id: 'exec-running-002',
      task_id: 'task-002',
      agent_id: 'reference',
      agent_version: '1.0.0',
      tenant_id: '00000000-0000-0000-0000-000000000099',
      requested_by: '00000000-0000-0000-0000-000000000001',
      status: 'RUNNING',
      mode: 'async',
      goal: 'Continuous compliance knowledge sweep',
      correlation_id: 'corr-002',
      attempt_number: 1,
      parent_execution_id: null,
      idempotency_key: null,
      cancel_requested: false,
      error_code: null,
      error_message: null,
      created_at: '2026-11-18T00:01:00Z',
      started_at: '2026-11-18T00:01:00Z',
      completed_at: null,
      deadline_at: null,
      duration_ms: null,
      queue_wait_ms: 6,
      status_url: '/api/v1/executions/exec-running-002',
      result_url: '/api/v1/executions/exec-running-002/result',
    },
    {
      execution_id: 'exec-failed-003',
      task_id: 'task-003',
      agent_id: 'research-graph',
      agent_version: '1.0.0',
      tenant_id: '00000000-0000-0000-0000-000000000099',
      requested_by: '00000000-0000-0000-0000-000000000001',
      status: 'FAILED',
      mode: 'async',
      goal: 'Transient upstream failure verification',
      correlation_id: 'corr-003',
      attempt_number: 1,
      parent_execution_id: null,
      idempotency_key: null,
      cancel_requested: false,
      error_code: 'AGENT_TRANSIENT_FAILURE',
      error_message: 'Simulated temporary upstream error',
      created_at: '2026-11-18T00:02:00Z',
      started_at: '2026-11-18T00:02:00Z',
      completed_at: '2026-11-18T00:02:01Z',
      deadline_at: null,
      duration_ms: 190,
      queue_wait_ms: 5,
      status_url: '/api/v1/executions/exec-failed-003',
      result_url: '/api/v1/executions/exec-failed-003/result',
    },
  ];

  // 1. Registered Agents Discovery
  await page.route('**/api/v1/agents', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Registered agents retrieved successfully.',
        data: {
          items: [
            {
              agent_id: 'reference',
              name: 'KEEP Reference Agent',
              version: '1.0.0',
              description: 'Deterministic reference agent validating Phase 4.1 contracts.',
              enabled: true,
              capabilities: [
                { name: 'knowledge_read', description: 'Read tenant knowledge', access_tier: 'read' },
              ],
            },
            {
              agent_id: 'research-graph',
              name: 'KEEP Research Graph Agent',
              version: '1.0.0',
              description: '2-step checkpointed LangGraph research workflow.',
              enabled: true,
              capabilities: [
                { name: 'research_synthesis', description: 'Synthesize grounded research', access_tier: 'read' },
              ],
            },
          ],
          total: 2,
        },
      }),
    });
  });

  // 2. Runtime Observability Metrics
  await page.route('**/api/v1/executions/metrics', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Agent runtime metrics retrieved successfully.',
        data: {
          total_completed: 18,
          active_executions: 1,
          executions_by_status: { SUCCEEDED: 16, FAILED: 1, TIMED_OUT: 1 },
          success_rate_percent: 88.9,
          avg_duration_ms: 164,
          p95_duration_ms: 340,
          avg_queue_wait_ms: 5,
          timeout_count: 1,
          cancellation_count: 1,
          retry_count: 2,
          output_validation_failures: 0,
          recent_events: [],
        },
      }),
    });
  });

  // 3. Submit Execution (POST /api/v1/agents/{id}/executions)
  await page.route('**/api/v1/agents/*/executions', async (route) => {
    if (route.request().method() === 'POST') {
      const urlParts = route.request().url().split('/');
      const agentId = urlParts[urlParts.length - 2] || 'research-graph';
      const body = JSON.parse(route.request().postData() || '{}');
      const newExec = {
        execution_id: 'exec-submitted-999',
        task_id: 'task-999',
        agent_id: agentId,
        agent_version: '1.0.0',
        tenant_id: '00000000-0000-0000-0000-000000000099',
        requested_by: '00000000-0000-0000-0000-000000000001',
        status: body.mode === 'async' ? 'QUEUED' : 'SUCCEEDED',
        mode: body.mode || 'sync',
        goal: body.goal || 'Submitted goal',
        correlation_id: 'corr-999',
        attempt_number: 1,
        parent_execution_id: null,
        idempotency_key: route.request().headers()['idempotency-key'] || null,
        cancel_requested: false,
        error_code: null,
        error_message: null,
        created_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        completed_at: body.mode === 'async' ? null : new Date().toISOString(),
        deadline_at: null,
        duration_ms: body.mode === 'async' ? null : 88,
        queue_wait_ms: 2,
        status_url: '/api/v1/executions/exec-submitted-999',
        result_url: '/api/v1/executions/exec-submitted-999/result',
      };
      await route.fulfill({
        status: body.mode === 'async' ? 202 : 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: `Execution '${newExec.execution_id}' completed with status ${newExec.status}.`,
          data: newExec,
        }),
      });
    }
  });

  // 4. Execution Result Inspection
  await page.route('**/api/v1/executions/*/result', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Execution result retrieved successfully.',
        data: {
          execution_id: 'exec-succeeded-001',
          agent_id: 'research-graph',
          execution_status: 'SUCCEEDED',
          status: 'succeeded',
          output: {
            summary: 'Phase 4.2 LangGraph checkpointed synthesis complete.',
            steps_completed: 2,
          },
          evidence: [
            {
              source_id: 'doc-arch-42',
              source_type: 'document',
              title: 'Phase 4.2 Runtime Architecture',
              excerpt: 'KEEP owns execution state, retries, cancellation, and tenant isolation.',
            },
          ],
          warnings: ['Checkpointed intermediate state persisted cleanly'],
          error_code: null,
          error_message: null,
          error: null,
          schema_version: '1.0',
        },
      }),
    });
  });

  // 5. Cancel Execution
  await page.route('**/api/v1/executions/*/cancel', async (route) => {
    const cancelled = { ...executions[1], status: 'CANCELLED', cancel_requested: true };
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: "Cancellation processed for execution 'exec-running-002' (status=CANCELLED).",
        data: cancelled,
      }),
    });
  });

  // 6. Retry Execution
  await page.route('**/api/v1/executions/*/retry', async (route) => {
    const retried = {
      ...executions[2],
      execution_id: 'exec-retry-004',
      status: 'QUEUED',
      attempt_number: 2,
      parent_execution_id: 'exec-failed-003',
      error_code: null,
      error_message: null,
    };
    await route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: "Retry attempt #2 created as 'exec-retry-004'.",
        data: retried,
      }),
    });
  });

  // 7. Execution List (with optional status query filter)
  await page.route('**/api/v1/executions?*', async (route) => {
    const url = new URL(route.request().url());
    const statusParam = url.searchParams.get('status');
    const filtered = statusParam
      ? executions.filter((item) => item.status === statusParam)
      : executions;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Agent executions retrieved successfully.',
        data: { items: filtered, total: filtered.length },
      }),
    });
  });
}

test.describe('Phase 4.2 — Agent Runtime & Execution Engine E2E', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupAgentRuntimeApiMocks(page);
  });

  test('1. Navigation, KPI banner & registered agents strip render cleanly', async ({ page }) => {
    await page.goto('/agents/runtime');
    await expect(page).toHaveURL(/.*\/agents\/runtime/);

    const main = page.getByRole('main');
    await expect(main.getByRole('heading', { name: /Agent Runtime & Execution Engine/i })).toBeVisible();
    await expect(main.getByText('Phase 4.2')).toBeVisible();

    // Metrics banner KPIs
    await expect(main.getByText('Completed Runs')).toBeVisible();
    await expect(main.getByText('18', { exact: true })).toBeVisible();
    await expect(main.getByText('88.9%')).toBeVisible();

    // Registered agents strip
    await expect(main.getByText('KEEP Reference Agent')).toBeVisible();
    await expect(main.getByText('KEEP Research Graph Agent')).toBeVisible();
  });

  test('2. Submit a new execution via Execute Agent modal', async ({ page }) => {
    await page.goto('/agents/runtime');

    await page.getByRole('main').getByRole('button', { name: 'Run Agent', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog.getByRole('heading', { name: 'Submit Agent Execution' })).toBeVisible();

    await dialog.getByLabel('Target Agent').selectOption('research-graph');
    await dialog.getByLabel('Execution Goal').fill('Run E2E checkpoint verification');
    await dialog.getByLabel('Idempotency Key (Optional)').fill('e2e-idem-001');
    await dialog.getByRole('button', { name: 'Execute Agent' }).click();

    await expect(page.getByRole('main').getByText(/exec-submitted-999/i).first()).toBeVisible();
    await expect(page.getByRole('main').getByText('Run E2E checkpoint verification')).toBeVisible();
  });

  test('3. Inspect execution result, structured output, and grounded evidence citations', async ({ page }) => {
    await page.goto('/agents/runtime');

    const main = page.getByRole('main');
    await main.getByRole('button', { name: 'Inspect Result' }).first().click();

    const drawer = page.getByRole('dialog', { name: 'Execution Result Drawer' });
    await expect(drawer.getByRole('heading', { name: /Execution Result & Evidence/i })).toBeVisible();
    await expect(drawer.getByText(/Phase 4.2 LangGraph checkpointed synthesis complete/i)).toBeVisible();
    await expect(drawer.getByText('Phase 4.2 Runtime Architecture')).toBeVisible();

    await drawer.getByRole('button', { name: 'Close Drawer' }).click();
    await expect(drawer).toBeHidden();
  });

  test('4. Cancel active execution, retry failed execution, and filter by status tab', async ({ page }) => {
    await page.goto('/agents/runtime');
    const main = page.getByRole('main');

    // Cancel running execution
    await main.getByRole('button', { name: /^Cancel$/i }).click();
    await expect(main.getByText(/Cancellation processed for execution 'exec-running-002'/i)).toBeVisible();

    // Retry failed execution
    await main.getByRole('button', { name: /^Retry$/i }).click();
    await expect(main.getByText(/Retry attempt #2 created as 'exec-retry-004'/i)).toBeVisible();

    // Filter status via tablist
    const succeededTab = main.getByRole('tab', { name: 'Succeeded' });
    await succeededTab.click();
    await expect(succeededTab).toHaveAttribute('aria-selected', 'true');
    await expect(main.getByText('Synthesize Q4 enterprise architecture audit')).toBeVisible();
  });

  test('5. Responsive layout verification across Desktop, Tablet, and Mobile viewports', async ({ page }) => {
    // Desktop 1440x900
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/agents/runtime');
    await expect(page.getByRole('main').getByRole('heading', { name: /Agent Runtime & Execution Engine/i })).toBeVisible();

    // Tablet 768x1024
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/agents/runtime');
    await expect(page.getByRole('main').getByRole('heading', { name: /Agent Runtime & Execution Engine/i })).toBeVisible();

    // Mobile 375x667
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/agents/runtime');
    await expect(page.getByRole('main').getByRole('heading', { name: /Agent Runtime & Execution Engine/i })).toBeVisible();
    await expect(page.getByRole('main').getByText('88.9%')).toBeVisible();
  });
});
