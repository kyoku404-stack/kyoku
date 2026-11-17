/**
 * KEEP Enterprise Platform — Phase 4.2 Agent Runtime & Execution Engine Types.
 *
 * Strictly aligned with backend Pydantic schemas in:
 * - backend/app/api/v1/agents.py
 * - backend/app/api/v1/agent_executions.py
 * - backend/app/agents/observability/telemetry.py
 */

export type ExecutionStatus =
  | 'PENDING'
  | 'QUEUED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'TIMED_OUT'
  | 'CANCELLED';

export type ExecutionMode = 'sync' | 'async';

export interface RegisteredAgentCapability {
  name: string;
  description: string;
  access_tier: 'read' | 'write' | 'sensitive' | string;
}

export interface RegisteredAgentItem {
  agent_id: string;
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  capabilities: RegisteredAgentCapability[];
  tags?: string[];
  max_timeout_seconds?: number;
}

export interface AgentListResponse {
  success: boolean;
  message: string;
  data: {
    items: RegisteredAgentItem[];
    total: number;
  };
}

export interface SubmitExecutionRequest {
  goal: string;
  input?: Record<string, unknown>;
  mode?: ExecutionMode;
  timeout_seconds?: number;
  idempotency_key?: string;
  requested_capabilities?: string[];
  correlation_id?: string;
}

export interface RetryExecutionRequest {
  mode?: ExecutionMode;
  timeout_seconds?: number;
}

export interface ExecutionRecordItem {
  execution_id: string;
  task_id: string;
  agent_id: string;
  agent_version: string;
  tenant_id: string;
  requested_by: string;
  status: ExecutionStatus;
  mode: ExecutionMode;
  goal: string;
  correlation_id: string;
  attempt_number: number;
  parent_execution_id: string | null;
  idempotency_key: string | null;
  cancel_requested: boolean;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  deadline_at: string | null;
  duration_ms: number | null;
  queue_wait_ms: number | null;
  status_url: string;
  result_url: string;
}

export interface ExecutionSingleResponse {
  success: boolean;
  message: string;
  data: ExecutionRecordItem;
}

export interface ExecutionListResponse {
  success: boolean;
  message: string;
  data: {
    items: ExecutionRecordItem[];
    total: number;
  };
}

export interface EvidenceReference {
  source_id: string;
  source_type: string;
  title?: string | null;
  excerpt?: string | null;
  confidence?: number | null;
  metadata?: Record<string, unknown>;
}

export interface AgentErrorDetail {
  code: string;
  message: string;
  retryable?: boolean;
  details?: Record<string, unknown>;
}

export interface ExecutionResultData {
  execution_id: string;
  agent_id: string;
  execution_status: ExecutionStatus;
  status: 'succeeded' | 'failed' | string;
  output: Record<string, unknown>;
  evidence: EvidenceReference[];
  warnings: string[];
  error_code: string | null;
  error_message: string | null;
  error: AgentErrorDetail | null;
  schema_version: string;
}

export interface ExecutionResultResponse {
  success: boolean;
  message: string;
  data: ExecutionResultData;
}

export interface ExecutionLifecycleEvent {
  event_type: string;
  execution_id: string;
  agent_id: string;
  agent_version: string;
  status: string;
  correlation_id: string;
  attempt_number: number;
  duration_ms: number | null;
  queue_wait_ms: number | null;
  error_code: string | null;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface RuntimeMetricsData {
  total_completed: number;
  active_executions: number;
  executions_by_status: Record<string, number>;
  success_rate_percent: number;
  avg_duration_ms: number;
  p95_duration_ms: number;
  avg_queue_wait_ms: number;
  timeout_count: number;
  cancellation_count: number;
  retry_count: number;
  output_validation_failures: number;
  recent_events: ExecutionLifecycleEvent[];
}

export interface RuntimeMetricsResponse {
  success: boolean;
  message: string;
  data: RuntimeMetricsData;
}
