/**
 * Phase 2.2 RAG Engine & Semantic Search TypeScript Definitions.
 * Aligned with docs/api/api-contract.md Section 9 and devdocs/p2/p2.2.txt.
 */

export interface RAGQueryRequest {
  query: string;
  session_id?: string | null;
  department_id?: string | null;
  project_id?: string | null;
  hybrid_dense_weight?: number;
  hybrid_sparse_weight?: number;
  top_k?: number;
  stream?: boolean;
}

export interface RAGCitation {
  citation_id: string;
  document_id: string;
  document_title: string;
  document_version_id?: string | null;
  page_number?: number | null;
  section?: string | null;
  chunk_id: string;
  similarity_score: number;
  excerpt: string;
}

export interface RAGRetrievalMetrics {
  dense_candidates: number;
  sparse_candidates: number;
  reranked_candidates: number;
  latency_retrieval_ms: number;
  latency_generation_ms: number;
  tokens_prompt: number;
  tokens_completion: number;
}

export interface RAGQueryResponse {
  query_id: string;
  session_id?: string | null;
  query: string;
  answer: string;
  confidence_score: number;
  is_grounded: boolean;
  processing_time_ms: number;
  citations: RAGCitation[];
  retrieval_metrics: RAGRetrievalMetrics;
}

export interface RAGChatMessageItem {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations_json?: string | null;
  created_at: string;
}

export interface RAGChatSessionItem {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages: RAGChatMessageItem[];
}

export interface RAGHistoryResponse {
  sessions: RAGChatSessionItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface RAGCitationDetail {
  citation_id: string;
  chunk_id: string;
  document_id: string;
  document_title: string;
  document_version_id?: string | null;
  chunk_index: number;
  page_number?: number | null;
  section?: string | null;
  full_content: string;
  metadata?: Record<string, unknown>;
}

export interface RAGFeedbackRequest {
  query_id: string;
  rating?: number | null;
  is_helpful: boolean;
  comment?: string | null;
}

export interface RAGFeedbackResponse {
  feedback_id: string;
  recorded_at: string;
}

export interface RAGStatistics {
  organization_id: string;
  total_queries: number;
  total_sessions: number;
  average_latency_ms: number;
  average_confidence_score: number;
  hallucination_refusal_count: number;
  positive_feedback_percentage: number;
  total_citations_rendered: number;
  cache_hit_ratio: number;
}
