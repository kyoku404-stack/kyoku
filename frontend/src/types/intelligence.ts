/**
 * Phase 2.5 Enterprise Intelligence & Predictive Analytics TypeScript Definitions.
 * Aligned with docs/api/api-contract.md Section 12 and devdocs/p2/p2.5.txt.
 * Author: Member 3 (Frontend & UI Lead)
 */

export type HealthScoreRating = 'EXCELLENT' | 'GOOD' | 'FAIR' | 'AT_RISK';

export type AnomalySeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type AnomalyType =
  | 'ACTIVITY_DROP'
  | 'UNUSUAL_LOGIN'
  | 'DELETION_BURST'
  | 'STORAGE_SPIKE'
  | 'API_FAILURE_SPIKE'
  | 'RETRIEVAL_DEGRADATION';

export type IntelligenceRecommendationCategory =
  | 'ARCHIVE'
  | 'DEDUPLICATE'
  | 'COVERAGE'
  | 'OWNERSHIP'
  | 'COLLABORATION'
  | 'SECURITY';

export type RecommendationCategory = IntelligenceRecommendationCategory;

export type RecommendationStatus = 'ACTIVE' | 'APPLIED' | 'DISMISSED';

export interface DepartmentHealthScoreItem {
  department: string;
  score: number;
  rating: HealthScoreRating | string;
  document_count: number;
}

export interface HealthScoreBreakdown {
  overall_score: number;
  rating: HealthScoreRating | string;
  coverage_score: number;
  freshness_score: number;
  quality_score: number;
  retrieval_score: number;
  duplicate_penalty: number;
  department_breakdown: DepartmentHealthScoreItem[];
  identified_gaps: string[];
}

export interface KPIsResponse {
  active_users: number;
  documents_uploaded: number;
  ai_queries: number;
  search_success_rate: number;
  avg_response_time_ms: number;
  storage_used_bytes: number;
  storage_capacity_bytes: number;
  knowledge_health_score: number;
}

export interface ExecutiveDashboardResponse {
  health_score: HealthScoreBreakdown;
  kpis: KPIsResponse;
  active_anomalies_count: number;
  top_recommendations_count: number;
  executive_summary: string;
}

export interface TrendPointItem {
  date: string;
  value: number;
}

export interface DepartmentActivityItem {
  department: string;
  document_count: number;
  query_count: number;
}

export interface TrendAnalysisResponse {
  period_days: number;
  document_growth: TrendPointItem[];
  ai_query_volume: TrendPointItem[];
  department_activity: DepartmentActivityItem[];
}

export interface DocumentForecastItem {
  current_value: number;
  projected_value: number;
  growth_rate_pct: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface StorageRunwayItem {
  current_usage_bytes: number;
  capacity_bytes: number;
  days_to_85_pct: number;
  days_to_full: number;
  is_critical: boolean;
}

export interface QueryVolumeForecastItem {
  current_daily_avg: number;
  projected_daily_avg: number;
  monthly_tokens_projected: number;
}

export interface PredictionsResponse {
  horizon_days: number;
  document_forecast: DocumentForecastItem;
  storage_runway: StorageRunwayItem;
  query_volume_forecast: QueryVolumeForecastItem;
}

export interface AnomalyResponseItem {
  id: string;
  metric_name: string;
  anomaly_type: AnomalyType | string;
  severity: AnomalySeverity | string;
  description: string;
  deviation_score: number;
  detected_at: string;
  resolved_at?: string | null;
}

export interface AnomaliesResponse {
  total_detected: number;
  anomalies: AnomalyResponseItem[];
}

export interface RecommendationResponseItem {
  id: string;
  category: RecommendationCategory | string;
  title: string;
  description: string;
  impact_score: number;
  effort_score: number;
  priority_index: number;
  status: RecommendationStatus | string;
  action_payload?: Record<string, unknown>;
}

export interface RecommendationsResponse {
  total_recommendations: number;
  recommendations: RecommendationResponseItem[];
}

export type KnowledgeHealthResponse = HealthScoreBreakdown;
