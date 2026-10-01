/**
 * KEEP Enterprise Platform — Chat & RAG Types.
 * Aligned with backend schemas (backend/app/schemas/chat.py).
 */

export interface ChatCitation {
  document_id: string;
  filename: string;
  page_number?: number | null;
  chunk_index?: number | null;
  snippet: string;
  relevance_score: number;
}

export interface ChatQueryRequest {
  query: string;
  conversation_id?: string | null;
  top_k?: number;
  include_citations?: boolean;
}

export interface ChatQueryResponse {
  query: string;
  answer: string;
  conversation_id: string;
  confidence_score: number;
  model_name: string;
  tokens_used: number;
  citations: ChatCitation[];
}

export interface ChatStreamRequest {
  query: string;
  conversation_id?: string | null;
}

/**
 * Server-Sent Events (SSE) streaming models for /api/v1/chat/stream.
 */
export interface SSETokenEvent {
  type: 'token';
  content: string;
}

export interface SSECitationEvent {
  type: 'citation';
  citations: ChatCitation[];
}

export interface SSEDoneEvent {
  type: 'done';
  conversation_id: string;
  total_tokens: number;
}

export interface SSEErrorEvent {
  type: 'error';
  error: string;
}

export type StreamEvent = SSETokenEvent | SSECitationEvent | SSEDoneEvent | SSEErrorEvent;

export interface ChatStreamCallbacks {
  onToken: (token: string) => void;
  onCitation?: (citations: ChatCitation[]) => void;
  onDone?: (data: { conversation_id: string; total_tokens: number }) => void;
  onError?: (error: Error) => void;
}
