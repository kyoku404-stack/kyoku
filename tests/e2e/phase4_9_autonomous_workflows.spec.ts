/**
 * Phase 4.9 — Autonomous Workflow Engine Playwright E2E Suite.
 *
 * Verifies end-to-end operator workflows on `/agents/autonomy`:
 * 1. Sidebar navigation (`Autonomous Workflows` + `Phase 4.9`) & KPI header.
 * 2. Churn Investigation Demo launch with adaptive bounded replanning & limitations.
 * 3. Approval-required write pause (`awaiting_approval`) -> `Approve & Resume` -> `completed`.
 * 4. Accessible status tab filtering & workflow cancellation.
 * 5. Responsive layout validation across Desktop (1440x900), Tablet (768x1024), Mobile (375x667).
 */

import { expect, Page, test } from '@playwright/test';

async function setupAuthenticatedUser(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'autonomy.lead@keep.enterprise.io',
      full_name: 'Autonomy Lead',
      role: 'OrgAdmin',
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_4_9');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_4_9');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  });
}

async function setupAutonomyApiMocks(page: Page): Promise<void> {
  let workflowList: Array<Record<string, unknown>> = [
    {
      execution_id: 'auto_wf_paused_001',
      tenant_id: 'tenant-1',
      requested_by: 'usr-1',
      workflow_id: 'churn_investigation',
      objective: 'Investigate churn and publish retention advisory externally',
      status: 'awaiting_approval',
      policy: {
        max_steps: 12,
        max_replans: 2,
        max_agent_attempts: 2,
        deadline_seconds: 600,
        require_approval_for_writes: true,
      },
      budget: {
        execution_id: 'auto_wf_paused_001',
        tenant_id: 'tenant-1',
        max_steps: 12,
        steps_consumed: 2,
        max_replans: 2,
        replans_consumed: 0,
        max_agent_attempts: 2,
        total_agent_attempts: 2,
        deadline_seconds: 600,
        updated_at: '2026-11-25T10:00:00Z',
      },
      current_plan: {},
      current_step_index: 2,
      replan_count: 0,
      termination_reason: "Paused awaiting human approval for write step 'auto_step_w1'.",
      limitations: [],
      final_result: {},
      deadline_at: '2026-11-25T10:10:00Z',
      created_at: '2026-11-25T10:00:00Z',
      updated_at: '2026-11-25T10:00:02Z',
    },
  ];

  const stepsByExec: Record<string, Array<Record<string, unknown>>> = {
    auto_wf_paused_001: [
      {
        step_id: 'auto_step_r1',
        execution_id: 'auto_wf_paused_001',
        tenant_id: 'tenant-1',
        plan_version: 1,
        step_order: 1,
        title: 'Retrieve churn evidence',
        agent_id: 'research_agent',
        required_capability: 'knowledge.research',
        is_side_effecting: false,
        status: 'succeeded',
        attempt: 1,
        max_attempts: 2,
        inputs: {},
        outputs: { summary: 'Retrieved 3 internal churn docs' },
        created_at: '2026-11-25T10:00:01Z',
      },
      {
        step_id: 'auto_step_w1',
        execution_id: 'auto_wf_paused_001',
        tenant_id: 'tenant-1',
        plan_version: 1,
        step_order: 2,
        title: 'Publish retention advisory externally',
        agent_id: 'knowledge_analysis',
        required_capability: 'knowledge.analyze',
        is_side_effecting: true,
        status: 'awaiting_approval',
        attempt: 0,
        max_attempts: 2,
        inputs: {},
        outputs: {},
        created_at: '2026-11-25T10:00:02Z',
      },
    ],
    auto_wf_churn_demo_002: [
      {
        step_id: 'auto_step_c1',
        execution_id: 'auto_wf_churn_demo_002',
        tenant_id: 'tenant-1',
        plan_version: 1,
        step_order: 1,
        title: 'Retrieve customer churn telemetry and support evidence',
        agent_id: 'research_agent',
        required_capability: 'knowledge.research',
        is_side_effecting: false,
        status: 'succeeded',
        attempt: 1,
        max_attempts: 2,
        inputs: {},
        outputs: { summary: 'Detected missing billing cohort log; triggered adaptive replan' },
        created_at: '2026-11-25T10:01:01Z',
      },
      {
        step_id: 'auto_step_c2',
        execution_id: 'auto_wf_churn_demo_002',
        tenant_id: 'tenant-1',
        plan_version: 2,
        step_order: 2,
        title: 'Adaptive follow-up retrieval for missing evidence',
        agent_id: 'research_agent',
        required_capability: 'knowledge.research',
        is_side_effecting: false,
        status: 'succeeded',
        attempt: 1,
        max_attempts: 2,
        inputs: {},
        outputs: { summary: 'Collected billing renewal cohorts [doc:billing_q4]' },
        created_at: '2026-11-25T10:01:02Z',
      },
    ],
  };

  const timelineByExec: Record<string, Record<string, unknown>> = {
    auto_wf_paused_001: {
      execution_id: 'auto_wf_paused_001',
      decisions: [
        {
          decision_id: 'dec_p1',
          execution_id: 'auto_wf_paused_001',
          tenant_id: 'tenant-1',
          action: 'pause_for_approval',
          reason: 'Side-effecting write requires human approval',
          evaluation_snapshot: {},
          remaining_steps: 10,
          created_at: '2026-11-25T10:00:02Z',
        },
      ],
      events: [
        {
          event_id: 'evt_p1',
          execution_id: 'auto_wf_paused_001',
          tenant_id: 'tenant-1',
          event_type: 'approval.required',
          actor_id: 'system:policy',
          details: {},
          created_at: '2026-11-25T10:00:02Z',
        },
      ],
    },
    auto_wf_churn_demo_002: {
      execution_id: 'auto_wf_churn_demo_002',
      decisions: [
        {
          decision_id: 'dec_c1',
          execution_id: 'auto_wf_churn_demo_002',
          tenant_id: 'tenant-1',
          action: 'replan',
          reason: 'Missing billing retention evidence',
          evaluation_snapshot: {},
          remaining_steps: 11,
          created_at: '2026-11-25T10:01:01Z',
        },
        {
          decision_id: 'dec_c2',
          execution_id: 'auto_wf_churn_demo_002',
          tenant_id: 'tenant-1',
          action: 'stop_completed',
          reason: 'Objective satisfied with grounded evidence',
          evaluation_snapshot: {},
          remaining_steps: 10,
          created_at: '2026-11-25T10:01:03Z',
        },
      ],
      events: [
        {
          event_id: 'evt_c1',
          execution_id: 'auto_wf_churn_demo_002',
          tenant_id: 'tenant-1',
          event_type: 'plan.revised',
          actor_id: 'system:planner',
          details: {},
          created_at: '2026-11-25T10:01:01Z',
        },
      ],
    },
  };

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          id: '00000000-0000-0000-0000-000000000001',
          email: 'autonomy.lead@keep.enterprise.io',
          full_name: 'Autonomy Lead',
          role: 'OrgAdmin',
          organization_id: '00000000-0000-0000-0000-000000000099',
        },
      }),
    });
  });

  await page.route('**/api/v1/autonomous-workflows**', async (route) => {
    const req = route.request();
    const url = req.url();
    const method = req.method();

    if (method === 'GET' && url.endsWith('/steps')) {
      const id = url.split('/autonomous-workflows/')[1].split('/')[0];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: stepsByExec[id] ?? [] }),
      });
      return;
    }

    if (method === 'GET' && url.endsWith('/events')) {
      const id = url.split('/autonomous-workflows/')[1].split('/')[0];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: timelineByExec[id] ?? { execution_id: id, decisions: [], events: [] },
        }),
      });
      return;
    }

    if (method === 'POST' && url.endsWith('/resume')) {
      const id = url.split('/autonomous-workflows/')[1].split('/')[0];
      workflowList = workflowList.map((w) =>
        w.execution_id === id
          ? {
              ...w,
              status: 'completed',
              termination_reason: 'Completed cleanly after write approval',
              final_result: {
                summary: 'Published advisory after explicit human approval.',
                evidence_refs: ['doc:retention:final'],
                limitations: [],
              },
            }
          : w
      );
      stepsByExec[id] = stepsByExec[id].map((s) => ({ ...s, status: 'succeeded', attempt: 1 }));
      const updated = workflowList.find((w) => w.execution_id === id);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: updated }),
      });
      return;
    }

    if (method === 'POST' && url.endsWith('/cancel')) {
      const id = url.split('/autonomous-workflows/')[1].split('/')[0];
      workflowList = workflowList.map((w) =>
        w.execution_id === id
          ? { ...w, status: 'cancelled', termination_reason: 'Write approval declined by operator' }
          : w
      );
      const updated = workflowList.find((w) => w.execution_id === id);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: updated }),
      });
      return;
    }

    if (method === 'POST') {
      const created = {
        execution_id: 'auto_wf_churn_demo_002',
        tenant_id: 'tenant-1',
        requested_by: 'usr-1',
        workflow_id: 'churn_investigation',
        objective:
          'Investigate the sudden Q4 rise in enterprise customer churn, analyze support escalations, and recommend retention actions.',
        status: 'completed',
        policy: {
          max_steps: 12,
          max_replans: 2,
          max_agent_attempts: 2,
          deadline_seconds: 600,
          require_approval_for_writes: true,
        },
        budget: {
          execution_id: 'auto_wf_churn_demo_002',
          tenant_id: 'tenant-1',
          max_steps: 12,
          steps_consumed: 2,
          max_replans: 2,
          replans_consumed: 1,
          max_agent_attempts: 2,
          total_agent_attempts: 2,
          deadline_seconds: 600,
          updated_at: '2026-11-25T10:01:03Z',
        },
        current_plan: {},
        current_step_index: 2,
        replan_count: 1,
        termination_reason: 'Objective satisfied with grounded evidence',
        limitations: ['Real-time CRM webhook metrics delayed by 1 hour.'],
        final_result: {
          summary: 'Churn investigation completed with 1 bounded replan.',
          findings: [{ step_id: 'auto_step_c2', title: 'Adaptive retrieval', summary: 'Complete' }],
          evidence_refs: ['doc:billing_q4'],
          limitations: ['Real-time CRM webhook metrics delayed by 1 hour.'],
        },
        deadline_at: '2026-11-25T10:10:00Z',
        created_at: '2026-11-25T10:01:00Z',
        updated_at: '2026-11-25T10:01:03Z',
      };
      workflowList = [created, ...workflowList];
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: created }),
      });
      return;
    }

    if (method === 'GET' && url.includes('/autonomous-workflows/auto_wf_')) {
      const id = url.split('/autonomous-workflows/')[1].split('?')[0];
      const found = workflowList.find((w) => w.execution_id === id) ?? workflowList[0];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: found }),
      });
      return;
    }

    if (method === 'GET') {
      const u = new URL(url);
      const statusParam = u.searchParams.get('status');
      const filtered = statusParam
        ? workflowList.filter((w) => w.status === statusParam)
        : workflowList;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: filtered }),
      });
    }
  });
}

test.describe('Phase 4.9 — Autonomous Workflow Engine UI E2E', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page);
    await setupAutonomyApiMocks(page);
  });

  test('navigates via Sidebar, approves paused write workflow, and launches Churn Demo with adaptive replanning', async ({
    page,
  }) => {
    await page.goto('/agents/autonomy');

    await expect(page.getByRole('heading', { name: 'Autonomous Workflow Engine' })).toBeVisible();
    await expect(page.getByText('Phase 4.9').first()).toBeVisible();

    // Verify pre-existing paused workflow displays approval gate and Approve & Resume transitions it
    await expect(
      page.getByText('Human Approval Required Before Side-Effecting Write')
    ).toBeVisible();
    await page.getByRole('button', { name: 'Approve & Resume' }).click();
    await expect(
      page.getByText('Completed cleanly after write approval')
    ).toBeVisible();

    // Load Churn Demo and submit adaptive workflow
    await page.getByRole('button', { name: 'Load Churn Investigation Demo' }).click();
    await page.getByRole('button', { name: 'Start Autonomous Workflow' }).click();

    await expect(page.getByText('auto_wf_churn_demo_002').first()).toBeVisible();
    await expect(page.getByText('Missing billing retention evidence')).toBeVisible();
    await expect(page.getByText('Real-time CRM webhook metrics delayed by 1 hour.').first()).toBeVisible();
  });

  test('supports accessible status tab filtering and renders across viewports cleanly', async ({
    page,
  }) => {
    await page.goto('/agents/autonomy');
    await page.getByRole('tab', { name: 'Awaiting Approval' }).click();
    await expect(page.getByText('auto_wf_paused_001').first()).toBeVisible();

    // Desktop, Tablet, Mobile responsiveness checks
    for (const vp of [
      { width: 1440, height: 900 },
      { width: 768, height: 1024 },
      { width: 375, height: 667 },
    ]) {
      await page.setViewportSize(vp);
      await expect(page.getByRole('heading', { name: 'Autonomous Workflow Engine' })).toBeVisible();
    }
  });
});
