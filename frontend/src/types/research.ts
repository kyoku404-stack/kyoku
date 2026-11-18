/**
 * KEEP Enterprise Platform — Phase 4.5 Research Agents TypeScript Contracts.
 *
 * Aligns strictly with `docs/API/api-contract.md` (Section 24) and
 * `backend/app/api/v1/research.py`.
 */

export type ResearchStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'partial'
  | 'insufficient_evidence'
  | 'failed'
  | 'cancelled';

export type RequiredOutputType = 'summary' | 'comparison' | 'detailed_report';

export type ConfidenceLevel = 'low' | 'medium' | 'high';

export type ClaimType = 'factual' | 'hypothesis' | 'recommendation';

export type ResearchAccessTier = 'read' | 'write' | 'sensitive';

export interface EvidenceItem {
  evidence_id: string;
  source_id: string;
  source_title: string;
  passage: string;
  retrieval_reference: string;
  relevance_score?: number | null;
  document_date?: string | null;
  access_tier: ResearchAccessTier;
  metadata?: Record<string, unknown>;
}

export interface ContradictionRecord {
  topic: string;
  description: string;
  evidence_ids: string[];
  source_dates: string[];
}

export interface ResearchFinding {
  finding_id: string;
  claim: string;
  claim_type: ClaimType;
  evidence_ids: string[];
  confidence: ConfidenceLevel;
  limitations: string[];
  has_contradiction: boolean;
}

export interface ResearchReport {
  research_id: string;
  question: string;
  scope?: string | null;
  required_output: RequiredOutputType;
  status: ResearchStatus;
  summary: string;
  findings: ResearchFinding[];
  evidence: EvidenceItem[];
  contradictions: ContradictionRecord[];
  unresolved_questions: string[];
  follow_up_suggestions: string[];
  warnings: string[];
  correction_attempts: number;
  sources_retrieved: number;
  sources_retained: number;
  retrieval_latency_ms?: number | null;
  synthesis_latency_ms?: number | null;
  correlation_id?: string | null;
  completed_at?: string | null;
  schema_version?: string;
}

export interface ResearchEventRecord {
  event_id: string;
  research_id: string;
  tenant_id: string;
  event_type: string;
  correlation_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface ResearchRunRecord {
  research_id: string;
  tenant_id: string;
  requested_by: string;
  question: string;
  scope?: string | null;
  required_output: RequiredOutputType;
  max_sources: number;
  status: ResearchStatus;
  summary?: string | null;
  contradictions: ContradictionRecord[];
  unresolved_questions: string[];
  follow_up_suggestions: string[];
  warnings: string[];
  correction_attempts: number;
  sources_retrieved: number;
  sources_retained: number;
  retrieval_latency_ms?: number | null;
  synthesis_latency_ms?: number | null;
  correlation_id: string;
  plan_id?: string | null;
  workflow_execution_id?: string | null;
  agent_execution_id?: string | null;
  idempotency_key?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StartResearchRequest {
  question: string;
  scope?: string;
  max_sources?: number;
  required_output?: RequiredOutputType;
  mode?: 'sync' | 'async';
  filters?: Record<string, unknown>;
  plan_id?: string;
  workflow_execution_id?: string;
}

export interface ResearchLaunchData {
  research_id: string;
  status: ResearchStatus;
  question: string;
  scope?: string | null;
  required_output: RequiredOutputType;
  max_sources: number;
  agent_execution_id?: string | null;
  correlation_id: string;
  status_url: string;
  report_url: string;
  evidence_url: string;
  report?: ResearchReport | null;
}

export interface ResearchLaunchResponse {
  success: boolean;
  message: string;
  data: ResearchLaunchData;
}

export interface ResearchListResponse {
  success: boolean;
  message: string;
  data: {
    items: ResearchRunRecord[];
    total: number;
  };
}

export interface ResearchRunDetailResponse {
  success: boolean;
  message: string;
  data: {
    run: ResearchRunRecord;
    events: ResearchEventRecord[];
  };
}

export interface ResearchReportResponse {
  success: boolean;
  message: string;
  data: ResearchReport;
}

export interface ResearchEvidenceResponse {
  success: boolean;
  message: string;
  data: {
    research_id: string;
    items: EvidenceItem[];
    total: number;
    redacted_count: number;
  };
}
