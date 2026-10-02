/**
 * KEEP Enterprise Platform — Analytics Types.
 * Aligned with backend schemas (backend/app/schemas/analytics.py).
 */

export interface AnalyticsSummaryResponse {
  total_documents: number;
  total_queries: number;
  total_users: number;
  active_sessions: number;
  storage_used_bytes: number;
}

export interface UsageMetricsResponse {
  queries_today: number;
  tokens_consumed_today: number;
  avg_latency_ms: number;
}
