/**
 * KEEP Enterprise Platform — Document Management Types.
 * Phase 1.8: Document Upload, File Management & Storage System.
 * Aligned with backend schemas (backend/app/schemas/document.py) and Phase 1.8 API contract (Section 6).
 */

// ─── Document Processing States ─────────────────────────────────────────────

export type DocumentProcessingState =
  | 'PENDING'
  | 'PROCESSING'
  | 'PROCESSED'
  | 'AWAITING_PROCESSING'
  | 'FAILED';

// ─── Document Categories ─────────────────────────────────────────────────────

export type DocumentCategory =
  | 'POLICIES'
  | 'REPORTS'
  | 'MEETING_MINUTES'
  | 'RESEARCH'
  | 'LEGAL'
  | 'FINANCE'
  | 'HR'
  | 'TECHNICAL_DOCUMENTATION'
  | 'PRESENTATIONS'
  | 'TRAINING_MATERIALS';

export const DOCUMENT_CATEGORIES: { value: DocumentCategory; label: string }[] = [
  { value: 'POLICIES', label: 'Policies' },
  { value: 'REPORTS', label: 'Reports' },
  { value: 'MEETING_MINUTES', label: 'Meeting Minutes' },
  { value: 'RESEARCH', label: 'Research' },
  { value: 'LEGAL', label: 'Legal' },
  { value: 'FINANCE', label: 'Finance' },
  { value: 'HR', label: 'HR' },
  { value: 'TECHNICAL_DOCUMENTATION', label: 'Technical Documentation' },
  { value: 'PRESENTATIONS', label: 'Presentations' },
  { value: 'TRAINING_MATERIALS', label: 'Training Materials' },
];

// ─── Supported MIME Types ────────────────────────────────────────────────────

export const SUPPORTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain',
  'text/markdown',
  'text/csv',
  'text/rtf',
  'image/png',
  'image/jpeg',
  'image/webp',
] as const;

export const SUPPORTED_EXTENSIONS = [
  '.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.md', '.csv', '.rtf', '.png', '.jpg', '.jpeg', '.webp',
];

export const MAX_FILE_SIZES: Record<string, number> = {
  'application/pdf': 100 * 1024 * 1024,
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 50 * 1024 * 1024,
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 100 * 1024 * 1024,
  default: 20 * 1024 * 1024,
};

// ─── Upload ──────────────────────────────────────────────────────────────────

export interface DocumentUploadPayload {
  file: File;
  title?: string;
  description?: string;
  category?: DocumentCategory;
  tags?: string[];
  project_id?: string;
}

/** Response from POST /api/v1/documents/upload (202 Accepted) */
export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  checksum_sha256: string;
  category: DocumentCategory;
  tags: string[];
  version_number: number;
  status: DocumentProcessingState;
  ai_ready: boolean;
  project_id: string | null;
  uploader_id: string | null;
  created_at: string;
}

// ─── Version History ─────────────────────────────────────────────────────────

/** A single version snapshot in the document's history */
export interface DocumentVersionItem {
  version_number: number;
  file_size: number;
  checksum_sha256: string;
  uploader_id: string;
  change_notes: string | null;
  created_at: string;
}

/** Response from POST /api/v1/documents/{id}/version (201 Created) */
export interface DocumentVersionUploadResponse {
  document_id: string;
  version_number: number;
  filename: string;
  file_size: number;
  checksum_sha256: string;
  change_notes: string | null;
  status: DocumentProcessingState;
  created_at: string;
}

// ─── Document List / Catalog Item ────────────────────────────────────────────

/** Lightweight representation used in paginated lists */
export interface DocumentItem {
  id: string;
  filename: string;
  title: string | null;
  file_type: string;
  file_size: number;
  category: string;
  tags: string[];
  version_number: number;
  status: DocumentProcessingState;
  ai_ready: boolean;
  chunk_count: number;
  project_id: string | null;
  uploader_id: string | null;
  uploader_name: string | null;
  created_at: string;
  updated_at: string | null;
}

// ─── Document Detail ─────────────────────────────────────────────────────────

/** Full document representation including metadata and version history */
export interface DocumentDetail extends DocumentItem {
  organization_id: string;
  original_filename: string;
  description: string | null;
  checksum_sha256: string;
  current_version_number: number;
  metadata_json: Record<string, unknown>;
  versions: DocumentVersionItem[];
}

// ─── Metadata Update ─────────────────────────────────────────────────────────

export interface DocumentUpdatePayload {
  title?: string;
  description?: string;
  category?: DocumentCategory;
  tags?: string[];
  project_id?: string;
}

export interface DocumentUpdateResponse {
  id: string;
  title: string | null;
  category: string;
  tags: string[];
  updated_at: string;
}

// ─── Delete / Archive ─────────────────────────────────────────────────────────

export interface DocumentDeleteResponse {
  id: string;
  deleted: boolean;
  is_deleted: boolean;
  deleted_at: string | null;
  status: string | null;
}

// ─── List Query Params ───────────────────────────────────────────────────────

export interface DocumentListParams {
  page?: number;
  page_size?: number;
  status?: DocumentProcessingState;
  category?: DocumentCategory;
  project_id?: string;
  search?: string;
  ai_ready?: boolean;
}

// ─── Legacy shim kept for backward compatibility ─────────────────────────────

/** @deprecated Use DocumentItem instead */
export interface DocumentResponse {
  id: string;
  organization_id?: string;
  uploader_id?: string;
  project_id?: string | null;
  filename: string;
  file_path?: string;
  file_type: string;
  file_size: number;
  status: DocumentProcessingState;
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
