import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import {
  AutonomousLaunchForm,
  AutonomousWorkflowInspector,
  AutonomousWorkflowList,
} from '@/features/autonomy';
import type {
  AutonomousStepRecord,
  AutonomousWorkflowRecord,
  AutonomyTimelineResponse,
} from '@/types/autonomy';

const SAMPLE_WORKFLOW: AutonomousWorkflowRecord = {
  execution_id: 'auto_wf_demo_01',
  tenant_id: 'tenant-1',
  requested_by: 'usr-1',
  workflow_id: 'churn_investigation',
  objective: 'Investigate Q4 customer churn increase',
  status: 'awaiting_approval',
  policy: {
    max_steps: 12,
    max_replans: 2,
    max_agent_attempts: 2,
    deadline_seconds: 600,
    require_approval_for_writes: true,
  },
  budget: {
    execution_id: 'auto_wf_demo_01',
    tenant_id: 'tenant-1',
    max_steps: 12,
    steps_consumed: 2,
    max_replans: 2,
    replans_consumed: 1,
    max_agent_attempts: 2,
    total_agent_attempts: 2,
    deadline_seconds: 600,
    updated_at: '2026-11-25T10:00:00Z',
  },
  current_plan: {},
  current_step_index: 2,
  replan_count: 1,
  termination_reason: 'Paused awaiting human approval for write step',
  limitations: ['Billing warehouse telemetry refreshed hourly.'],
  final_result: {
    summary: 'Churn spiked 18% due to retry storm.',
    evidence_refs: ['doc:churn_q4:p1'],
    limitations: ['Billing warehouse telemetry refreshed hourly.'],
  },
  deadline_at: '2026-11-25T10:10:00Z',
  created_at: '2026-11-25T10:00:00Z',
  updated_at: '2026-11-25T10:00:05Z',
};

const SAMPLE_STEPS: AutonomousStepRecord[] = [
  {
    step_id: 'auto_step_1',
    execution_id: 'auto_wf_demo_01',
    tenant_id: 'tenant-1',
    plan_version: 1,
    step_order: 1,
    title: 'Retrieve churn telemetry',
    agent_id: 'research_agent',
    required_capability: 'knowledge.research',
    is_side_effecting: false,
    status: 'succeeded',
    attempt: 1,
    max_attempts: 2,
    inputs: {},
    outputs: { summary: 'Retrieved 4 cohort logs' },
    created_at: '2026-11-25T10:00:01Z',
  },
  {
    step_id: 'auto_step_2',
    execution_id: 'auto_wf_demo_01',
    tenant_id: 'tenant-1',
    plan_version: 2,
    step_order: 2,
    title: 'Publish retention advisory',
    agent_id: 'knowledge_analysis',
    required_capability: 'knowledge.analyze',
    is_side_effecting: true,
    status: 'awaiting_approval',
    attempt: 0,
    max_attempts: 2,
    inputs: {},
    outputs: {},
    created_at: '2026-11-25T10:00:03Z',
  },
];

const SAMPLE_TIMELINE: AutonomyTimelineResponse = {
  execution_id: 'auto_wf_demo_01',
  decisions: [
    {
      decision_id: 'auto_dec_1',
      execution_id: 'auto_wf_demo_01',
      tenant_id: 'tenant-1',
      action: 'replan',
      reason: 'Missing billing cancellation cohort evidence',
      evaluation_snapshot: {},
      remaining_steps: 10,
      created_at: '2026-11-25T10:00:02Z',
    },
  ],
  events: [
    {
      event_id: 'auto_evt_1',
      execution_id: 'auto_wf_demo_01',
      tenant_id: 'tenant-1',
      event_type: 'approval.required',
      actor_id: 'system:policy',
      details: {},
      created_at: '2026-11-25T10:00:03Z',
    },
  ],
};

describe('Phase 4.9 Autonomous Workflow Components', () => {
  it('loads Churn Investigation demo and submits bounded AutonomousLaunchForm', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<AutonomousLaunchForm isSubmitting={false} canInvoke={true} onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: /Load Churn Investigation Demo/i }));
    fireEvent.click(screen.getByRole('button', { name: /Start Autonomous Workflow/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        workflow_id: 'churn_investigation',
        objective: expect.stringContaining('customer churn'),
      })
    );
  });

  it('filters workflows via accessible role=tab controls and selects an execution', () => {
    const onFilterChange = vi.fn();
    const onSelect = vi.fn();
    render(
      <AutonomousWorkflowList
        workflows={[SAMPLE_WORKFLOW]}
        selectedExecutionId="auto_wf_demo_01"
        statusFilter="all"
        isLoading={false}
        onFilterChange={onFilterChange}
        onSelect={onSelect}
        onRefresh={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('tab', { name: /Awaiting Approval/i }));
    expect(onFilterChange).toHaveBeenCalledWith('awaiting_approval');

    fireEvent.click(screen.getByText(/Investigate Q4 customer churn increase/i));
    expect(onSelect).toHaveBeenCalledWith('auto_wf_demo_01');
  });

  it('displays approval gate banner and invokes Approve & Resume or Reject & Cancel', async () => {
    const onResume = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn().mockResolvedValue(undefined);
    render(
      <AutonomousWorkflowInspector
        workflow={SAMPLE_WORKFLOW}
        steps={SAMPLE_STEPS}
        timeline={SAMPLE_TIMELINE}
        canInvoke={true}
        isUpdatingAction={false}
        onResume={onResume}
        onCancel={onCancel}
      />
    );

    expect(screen.getByRole('alert')).toHaveTextContent(
      /Human Approval Required Before Side-Effecting Write/i
    );
    expect(screen.getByText(/Missing billing cancellation cohort evidence/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Approve & Resume/i }));
    expect(onResume).toHaveBeenCalledWith(
      'auto_wf_demo_01',
      true,
      expect.stringContaining('Approved')
    );

    fireEvent.click(screen.getByRole('button', { name: /Reject & Cancel/i }));
    expect(onCancel).toHaveBeenCalledWith(
      'auto_wf_demo_01',
      expect.stringContaining('declined')
    );
  });
});
