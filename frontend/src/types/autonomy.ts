/**
 * KEEP Enterprise Platform — Phase 4.9 Autonomous Workflow Engine Types.
 */

import type { ApiResponse } from './api';

export type AutonomyStatus =
  | 'pending'
  | 'running'
  | 'awaiting_approval'
  | 'completed'
  | 'failed'
  | 'budget_exhausted'
  | 'cancelled';

export type StepStatus =
  | 'pending'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'skipped'
  | 'awaiting_approval'
  | 'cancelled';

export type DecisionAction =
  | 'continue'
  | 'replan'
  | 'pause_for_approval'
  | 'stop_completed'
  | 'stop_failed'
  | 'stop_budget_exhausted'
  | 'stop_cancelled';

export interface AutonomyPolicy {
  max_steps: number;
  max_replans: number;
  max_agent_attempts: number;
  deadline_seconds: number;
  require_approval_for_writes: boolean;
  allowed_agents?: string[];
  allowed_tools?: string[];
}

export interface AutonomousWorkflowRequest {
  objective: string;
  workflow_id: string;
  policy?: Partial<AutonomyPolicy>;
  mode?: 'sync' | 'async';
  idempotency_key?: string;
}

export interface AutonomyBudgetSnapshot {
  execution_id: string;
  tenant_id: string;
  max_steps: number;
  steps_consumed: number;
  max_replans: number;
  replans_consumed: number;
  max_agent_attempts: number;
  total_agent_attempts: number;
  deadline_seconds: number;
  updated_at: string;
}

export interface AutonomousStepRecord {
  step_id: string;
  execution_id: string;
  tenant_id: string;
  plan_version: number;
  step_order: number;
  title: string;
  agent_id: string;
  tool_id?: string | null;
  required_capability: string;
  is_side_effecting: boolean;
  status: StepStatus;
  attempt: number;
  max_attempts: number;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  error_code?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface AutonomyDecisionRecord {
  decision_id: string;
  execution_id: string;
  tenant_id: string;
  action: DecisionAction;
  reason: string;
  evaluation_snapshot: Record<string, unknown>;
  remaining_steps: number;
  created_at: string;
}

export interface AutonomyEventRecord {
  event_id: string;
  execution_id: string;
  tenant_id: string;
  event_type: string;
  actor_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AutonomyTimelineResponse {
  execution_id: string;
  decisions: AutonomyDecisionRecord[];
  events: AutonomyEventRecord[];
}

export interface AutonomyFinalReport {
  summary?: string;
  findings?: Array<{
    step_id?: string;
    title?: string;
    agent_id?: string;
    summary?: string;
  }>;
  evidence_refs?: string[];
  limitations?: string[];
  termination_reason?: string;
  confidence?: number;
}

export interface AutonomousWorkflowRecord {
  execution_id: string;
  tenant_id: string;
  requested_by: string;
  workflow_id: string;
  objective: string;
  status: AutonomyStatus;
  policy: AutonomyPolicy;
  budget?: AutonomyBudgetSnapshot | null;
  current_plan: Record<string, unknown>;
  current_step_index: number;
  replan_count: number;
  termination_reason?: string | null;
  limitations: string[];
  final_result: AutonomyFinalReport & Record<string, unknown>;
  checkpoint_ref?: string | null;
  deadline_at: string;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

export interface CancelWorkflowRequest {
  reason: string;
}

export interface ResumeWorkflowRequest {
  approve: boolean;
  reason: string;
}

export type AutonomousWorkflowResponse = ApiResponse<AutonomousWorkflowRecord>;
export type AutonomousWorkflowListResponse = ApiResponse<AutonomousWorkflowRecord[]>;
export type AutonomousStepsResponse = ApiResponse<AutonomousStepRecord[]>;
export type AutonomousTimelineApiResponse = ApiResponse<AutonomyTimelineResponse>;
