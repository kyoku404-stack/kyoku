/**
 * KEEP Enterprise Platform — Chat, RAG & Feedback Types.
 * Aligned with backend schemas and `chat_sessions`, `chat_messages`, `ai_feedback` tables.
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
  project_id?: string | null;
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
  project_id?: string | null;
}

export interface ChatSessionResponse {
  id: string;
  organization_id: string;
  user_id: string;
  project_id?: string | null;
  title: string;
  is_archived: boolean;
  message_count?: number;
  created_at: string;
  updated_at?: string | null;
}

export interface ChatMessageResponse {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  model_name?: string | null;
  tokens_prompt: number;
  tokens_completion: number;
  latency_ms: number;
  citations: ChatCitation[];
  created_at: string;
}

export interface AIFeedbackCreate {
  message_id: string;
  rating: 1 | -1;
  comment?: string;
}

export interface AIFeedbackResponse {
  id: string;
  message_id: string;
  user_id: string;
  rating: number;
  comment?: string | null;
  created_at: string;
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
