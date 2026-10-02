/**
 * KEEP Enterprise Platform — Search Types.
 * Aligned with backend schemas (backend/app/schemas/search.py).
 */

export interface SearchFilter {
  document_types?: string[];
  document_ids?: string[];
}

export interface HybridSearchRequest {
  query: string;
  top_k?: number;
  filters?: SearchFilter | null;
}

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number?: number | null;
  content: string;
  relevance_score: number;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResultItem[];
}
