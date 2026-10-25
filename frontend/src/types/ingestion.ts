/**
 * KEEP Enterprise Platform — AI Knowledge Ingestion Pipeline Types (Phase 2.1).
 *
 * Defines strongly-typed TypeScript interfaces, enums, request payloads,
 * and response models for document ingestion, real-time stage monitoring,
 * and operational pipeline metrics.
 *
 * Specification: devdocs/p2/p2.1.txt & docs/api/api-contract.md Section 8
 * Author: Member 3 (Frontend Lead)
 */

import type { ApiResponse, PaginatedData } from './api';

// ─── Pipeline Enums ──────────────────────────────────────────────────────────

/**
 * 10-stage lifecycle status of an ingestion job.
 * Conforms to backend IngestionJobStatus in backend/app/services/ai/ingestion.py
 */
export enum IngestionJobStatus {
  PENDING = 'PENDING',
  EXTRACTING = 'EXTRACTING',
  OCR_PROCESSING = 'OCR_PROCESSING',
  NORMALIZING = 'NORMALIZING',
  CHUNKING = 'CHUNKING',
  EMBEDDING = 'EMBEDDING',
  INDEXING = 'INDEXING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  RETRYING = 'RETRYING',
}

/**
 * Chunking strategies supported by KEEP AI Ingestion Engine.
 * Conforms to ADR-032.
 */
export enum ChunkingStrategy {
  SEMANTIC_HEADING_AWARE = 'SEMANTIC_HEADING_AWARE',
  FIXED_TOKEN_OVERLAP = 'FIXED_TOKEN_OVERLAP',
  PARAGRAPH_BOUNDARY = 'PARAGRAPH_BOUNDARY',
  HIERARCHICAL_RECURSIVE = 'HIERARCHICAL_RECURSIVE',
  DOCUMENT_STRUCTURE_AWARE = 'DOCUMENT_STRUCTURE_AWARE',
}

/**
 * Supported embedding model providers for vector synthesis.
 * Conforms to ADR-033.
 */
export enum EmbeddingModelProvider {
  OPENAI = 'OPENAI',
  LOCAL_BGE = 'LOCAL_BGE',
  COHERE = 'COHERE',
  VOYAGE = 'VOYAGE',
  HUGGINGFACE = 'HUGGINGFACE',
}

// ─── Request Payloads ────────────────────────────────────────────────────────

/**
 * Payload sent to POST /api/v1/ingestion/start to initiate processing.
 */
export interface StartIngestionRequest {
  document_id: string;
  document_version_id?: string;
  force_ocr?: boolean;
  chunking_strategy?: ChunkingStrategy;
  target_chunk_size?: number;
  chunk_overlap?: number;
  embedding_provider?: EmbeddingModelProvider;
  embedding_model?: string;
}

/**
 * Query parameters for filtering GET /api/v1/ingestion/jobs.
 */
export interface IngestionJobListParams {
  page?: number;
  page_size?: number;
  status?: IngestionJobStatus | string;
  document_id?: string;
}

// ─── Response Data Models ────────────────────────────────────────────────────

/**
 * Data payload returned upon POST /api/v1/ingestion/start (202 Accepted).
 */
export interface StartIngestionResponseData {
  job_id: string;
  document_id: string;
  status: IngestionJobStatus | string;
  queue_name: string;
  enqueued_at: string;
}

/**
 * Data payload returned from GET /api/v1/ingestion/status/{id} (200 OK).
 */
export interface IngestionJobStatusResponseData {
  job_id: string;
  document_id: string;
  status: IngestionJobStatus | string;
  progress_percent: number;
  current_stage: string;
  total_pages: number;
  processed_pages: number;
  chunks_generated: number;
  embeddings_generated: number;
  ocr_applied: boolean;
  retry_count: number;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds: number;
}

/**
 * Summary item in GET /api/v1/ingestion/jobs paginated response.
 */
export interface IngestionJobListItem {
  job_id: string;
  document_id: string;
  document_title: string;
  status: IngestionJobStatus | string;
  chunks_generated: number;
  duration_seconds: number;
  created_at: string;
  completed_at?: string | null;
}

/**
 * Data payload returned upon POST /api/v1/ingestion/retry/{id} (200 OK).
 */
export interface IngestionRetryResponseData {
  job_id: string;
  status: IngestionJobStatus | string;
  retry_count: number;
  enqueued_at: string;
}

/**
 * Tenant-wide operational metrics from GET /api/v1/ingestion/statistics (200 OK).
 */
export interface IngestionStatisticsResponseData {
  organization_id: string;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  pending_jobs: number;
  total_chunks_indexed: number;
  average_duration_seconds: number;
  average_throughput_pages_per_minute: number;
  ocr_utilization_percent: number;
  retry_success_rate_percent: number;
}

// ─── Type Aliases for API Envelopes ──────────────────────────────────────────

export type StartIngestionApiResponse = ApiResponse<StartIngestionResponseData>;
export type IngestionStatusApiResponse = ApiResponse<IngestionJobStatusResponseData>;
export type IngestionJobsApiResponse = ApiResponse<PaginatedData<IngestionJobListItem>>;
export type IngestionRetryApiResponse = ApiResponse<IngestionRetryResponseData>;
export type IngestionStatisticsApiResponse = ApiResponse<IngestionStatisticsResponseData>;
