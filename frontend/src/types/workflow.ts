/**
 * KEEP Enterprise Platform — Workflow Automation & Event-Driven Intelligence Types.
 * Phase 3.4 Domain Models aligned with backend Pydantic schemas and Section 16 API contracts.
 */

export type WorkflowTriggerType =
  | 'document_created'
  | 'document_updated'
  | 'security_anomaly'
  | 'connector_synced'
  | 'meeting_completed'
  | 'manual'
  | 'scheduled';

export type WorkflowStatus = 'active' | 'inactive' | 'draft' | 'archived';

export type WorkflowExecutionStatus =
  | 'pending'
  | 'running'
  | 'waiting_approval'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type WorkflowStepAction =
  | 'send_notification'
  | 'invoke_llm'
  | 'http_webhook'
  | 'trigger_connector_sync'
  | 'request_approval'
  | 'execute_rag_query';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired';
export type ApprovalDecision = 'approved' | 'rejected';

export type NotificationChannel = 'in_app' | 'email' | 'slack' | 'teams';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type NotificationCategory = 'workflow' | 'security' | 'system' | 'task';

export interface WorkflowConditionRule {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'in';
  value: unknown;
}

export interface WorkflowRetryPolicy {
  max_attempts: number;
  initial_delay_seconds: number;
  backoff_multiplier: number;
}

export interface WorkflowStepItem {
  id?: string;
  workflow_id?: string;
  step_order: number;
  name: string;
  description?: string;
  action_type: WorkflowStepAction;
  action_config: Record<string, unknown>;
  retry_policy?: WorkflowRetryPolicy;
  timeout_seconds?: number;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowItem {
  id: string;
  organization_id: string;
  created_by_id: string;
  name: string;
  description?: string;
  trigger_type: WorkflowTriggerType;
  trigger_config: Record<string, unknown>;
  condition_rules: WorkflowConditionRule[];
  is_active: boolean;
  execution_count: number;
  success_count: number;
  created_at: string;
  updated_at: string;
  steps: WorkflowStepItem[];
}

export interface WorkflowCreatePayload {
  name: string;
  description?: string;
  trigger_type: WorkflowTriggerType;
  trigger_config?: Record<string, unknown>;
  condition_rules?: WorkflowConditionRule[];
  is_active?: boolean;
  steps: Array<{
    step_order: number;
    name: string;
    description?: string;
    action_type: WorkflowStepAction;
    action_config?: Record<string, unknown>;
    retry_policy?: WorkflowRetryPolicy;
    timeout_seconds?: number;
  }>;
}

export interface WorkflowUpdatePayload {
  name?: string;
  description?: string;
  is_active?: boolean;
  trigger_config?: Record<string, unknown>;
  condition_rules?: WorkflowConditionRule[];
}

export interface WorkflowExecutionStepItem {
  id: string;
  execution_id: string;
  step_id?: string;
  step_order: number;
  step_name: string;
  action_type: WorkflowStepAction;
  status: WorkflowExecutionStatus;
  input_payload?: Record<string, unknown>;
  output_payload?: Record<string, unknown>;
  error_details?: string;
  attempts: number;
  execution_time_ms: number;
  started_at?: string;
  completed_at?: string;
}

export interface WorkflowExecutionItem {
  id: string;
  workflow_id: string;
  trigger_event: string;
  status: WorkflowExecutionStatus;
  context_data: Record<string, unknown>;
  trigger_metadata: Record<string, unknown>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_ms: number;
  steps?: WorkflowExecutionStepItem[];
}

export interface WorkflowApprovalItem {
  id: string;
  execution_id: string;
  step_id?: string;
  workflow_name?: string;
  step_name?: string;
  status: ApprovalStatus;
  decision?: ApprovalDecision;
  comments?: string;
  requested_approver_id?: string;
  approved_by_id?: string;
  decided_at?: string;
  expires_at?: string;
  created_at: string;
}

export interface WorkflowApprovalDecisionPayload {
  decision: ApprovalDecision;
  comments?: string;
}

export interface NotificationItem {
  id: string;
  organization_id: string;
  user_id: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  category: NotificationCategory;
  title: string;
  content: string;
  link_url?: string;
  is_read: boolean;
  read_at?: string;
  metadata_json?: Record<string, unknown>;
  created_at: string;
}

export interface NotificationPreferenceItem {
  category: NotificationCategory;
  in_app: boolean;
  email: boolean;
  slack: boolean;
  teams: boolean;
}

export interface NotificationPreferenceUpdatePayload {
  category: NotificationCategory;
  in_app?: boolean;
  email?: boolean;
  slack?: boolean;
  teams?: boolean;
}

export interface WorkflowTemplateItem {
  id: string;
  name: string;
  description: string;
  category: string;
  complexity: 'simple' | 'medium' | 'advanced';
  is_built_in: boolean;
  trigger_type: WorkflowTriggerType;
  condition_rules: WorkflowConditionRule[];
  steps_template: WorkflowStepItem[];
  created_at: string;
}

export interface WorkflowAnalyticsData {
  total_workflows: number;
  active_workflows: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  average_duration_ms: number;
  pending_approvals_count: number;
  executions_by_day: Array<{
    date: string;
    count: number;
    success: number;
    failed: number;
  }>;
}
