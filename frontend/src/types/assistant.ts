/**
 * Phase 2.3 Enterprise AI Assistant & Agentic Workflows TypeScript Definitions.
 * Aligned with docs/api/api-contract.md Section 10 and devdocs/p2/p2.3.txt.
 * Author: Member 3 (Frontend Lead)
 */

export type AssistantIntent =
  | 'KNOWLEDGE_QA'
  | 'DOCUMENT_SUMMARIZATION'
  | 'REPORT_GENERATION'
  | 'ACTION_EXECUTION'
  | 'RECOMMENDATION_DISCOVERY'
  | 'CONVERSATIONAL_FOLLOWUP';

export type WorkflowStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'WAITING_APPROVAL'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type TaskStepStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'WAITING_APPROVAL'
  | 'COMPLETED'
  | 'FAILED'
  | 'SKIPPED';

export type ApprovalDecision = 'APPROVED' | 'REJECTED';

export type ReportType =
  | 'MEETING_SUMMARY'
  | 'WEEKLY_ROLLUP'
  | 'PROJECT_STATUS'
  | 'DEPARTMENT_ANALYTICS'
  | 'KNOWLEDGE_SYNTHESIS';

export type ReportFormat = 'MARKDOWN' | 'PDF' | 'DOCX' | 'JSON';

export type RecommendationCategory =
  | 'FREQUENT_DOCUMENTS'
  | 'MISSING_DOCUMENTATION'
  | 'DUPLICATE_KNOWLEDGE'
  | 'INACTIVE_PROJECTS';

export interface AssistantChatRequest {
  message: string;
  session_id?: string | null;
  department_id?: string | null;
  project_id?: string | null;
}

export interface AssistantChatResponseData {
  session_id: string;
  message_id: string;
  reply: string;
  detected_intent: AssistantIntent;
  workflow_id?: string | null;
  tools_executed: string[];
  requires_approval: boolean;
  approval_id?: string | null;
  created_at: string;
}

export interface TaskExecuteRequest {
  instructions: string;
  title?: string | null;
  session_id?: string | null;
  context?: Record<string, unknown>;
}

export interface TaskStepResponse {
  step_number: number;
  tool_name: string;
  description: string;
  status: TaskStepStatus;
  latency_ms: number;
  output?: Record<string, unknown> | null;
  error?: string | null;
  approval_id?: string | null;
}

export interface TaskExecuteResponseData {
  workflow_id: string;
  title: string;
  status: WorkflowStatus;
  total_steps: number;
  completed_steps: number;
  steps: TaskStepResponse[];
  result_summary?: string | null;
  pending_approval?: {
    approval_id: string;
    step_number: number;
    action_type: string;
    description: string;
    payload: Record<string, unknown>;
    status: string;
  } | null;
}

export interface ReportGenerateRequest {
  report_type: ReportType;
  title: string;
  format?: ReportFormat;
  filters?: Record<string, unknown>;
}

export interface ReportGenerateResponseData {
  report_id: string;
  report_type: ReportType;
  title: string;
  format: ReportFormat;
  content: string;
  created_at: string;
}

export interface WorkflowItemResponse {
  id: string;
  title: string;
  trigger_type: string;
  status: WorkflowStatus;
  total_steps: number;
  completed_steps: number;
  created_at: string;
  completed_at?: string | null;
}

export interface WorkflowListResponseData {
  workflows: WorkflowItemResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApprovalActionRequest {
  approval_id: string;
  decision: ApprovalDecision;
  reason?: string | null;
}

export interface ApprovalActionResponseData {
  approval_id: string;
  workflow_id?: string | null;
  decision: ApprovalDecision;
  status: string;
  executed_at: string;
}

export interface ProactiveRecommendationItem {
  id: string;
  category: RecommendationCategory;
  title: string;
  description: string;
  suggested_action: string;
  metadata?: Record<string, unknown>;
}

export interface RecommendationResponseData {
  recommendations: ProactiveRecommendationItem[];
}

export interface AssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: AssistantIntent;
  tools_executed?: string[];
  requires_approval?: boolean;
  approval_id?: string | null;
  created_at: string;
}

export interface AssistantMetrics {
  active_workflows: number;
  pending_approvals: number;
  tasks_automated: number;
  reports_generated: number;
}
