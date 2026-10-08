/**
 * KEEP Enterprise Platform — Document Ingestion & Chunk Vector Types.
 * Aligned with backend schemas (backend/app/schemas/document.py) and `documents`/`document_chunks` tables.
 */

export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'PROCESSED' | 'FAILED';

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  file_size: number;
  created_at: string;
}

export interface DocumentResponse {
  id: string;
  organization_id?: string;
  uploader_id?: string;
  project_id?: string | null;
  filename: string;
  file_path?: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  chunk_count: number;
  error_message?: string | null;
  metadata_json?: Record<string, unknown>;
  is_deleted?: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface DocumentChunk {
  id: string;
  organization_id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  page_number?: number | null;
  section_title?: string | null;
  metadata_json?: Record<string, unknown>;
  created_at: string;
}

export interface DocumentListParams {
  page?: number;
  page_size?: number;
  status?: DocumentStatus;
  project_id?: string;
  search?: string;
}
