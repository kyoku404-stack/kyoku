/**
 * KEEP Enterprise Platform — Phase 4.11 Proactive Enterprise Intelligence Types.
 */

export type InsightCategory =
  | 'knowledge_gap'
  | 'contradiction'
  | 'stale_knowledge'
  | 'significant_change'
  | 'emerging_trend';

export type InsightStatus =
  | 'candidate'
  | 'validated'
  | 'published'
  | 'suppressed'
  | 'withheld'
  | 'investigating'
  | 'dismissed'
  | 'resolved';

export type FeedbackType =
  | 'useful'
  | 'irrelevant'
  | 'already_known'
  | 'incorrect'
  | 'needs_more_evidence';

export interface EvidenceReference {
  evidence_id: string;
  resource_ref: string;
  source_type: string;
  source_version?: string | null;
  snippet?: string | null;
  validation_outcome: 'valid' | 'missing' | 'unauthorized' | 'stale';
  verified_at: string;
}

export interface IntelligenceInsight {
  insight_id: string;
  tenant_id: string;
  run_id: string;
  category: InsightCategory;
  title: string;
  summary: string;
  observed_facts: string[];
  inferred_explanation?: string | null;
  limitations: string[];
  evidence_refs: string[];
  evidence_records: EvidenceReference[];
  affected_resource_refs: string[];
  audience_roles: string[];
  impact_score: number;
  relevance_score: number;
  evidence_quality_score: number;
  urgency_score: number;
  novelty_score: number;
  priority_score: number;
  confidence_score: number;
  status: InsightStatus;
  dedup_key: string;
  detector_id: string;
  detector_version: string;
  ranking_version: string;
  workflow_execution_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DetectionRunRecord {
  run_id: string;
  tenant_id: string;
  trigger_source: 'manual' | 'event' | 'schedule';
  source_event_id?: string | null;
  detector_versions: Record<string, string>;
  status: 'running' | 'completed' | 'completed_with_errors' | 'failed';
  candidates_generated: number;
  insights_published: number;
  insights_suppressed: number;
  detector_errors: Array<{ detector_id: string; error: string }>;
  started_at: string;
  completed_at?: string | null;
}

export interface OperationalMetrics {
  tenant_id: string;
  total_runs: number;
  total_candidates: number;
  published_insights: number;
  suppressed_insights: number;
  withheld_insights: number;
  dismissed_insights: number;
  resolved_insights: number;
  duplicate_suppression_rate: number;
  feedback_counts: Record<string, number>;
  category_counts: Record<string, number>;
}

export interface ScanRequest {
  observations: Array<Record<string, unknown>>;
  detector_ids?: string[];
  trigger_source?: 'manual' | 'event' | 'schedule';
  suppress_window_seconds?: number;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message?: string | null;
}
