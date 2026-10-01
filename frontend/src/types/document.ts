/**
 * KEEP Enterprise Platform — Document Ingestion Types.
 * Aligned with backend schemas (backend/app/schemas/document.py) and constants (backend/app/core/constants.py).
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
  filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
  updated_at?: string | null;
}

export interface DocumentListParams {
  page?: number;
  page_size?: number;
  status?: DocumentStatus;
}
