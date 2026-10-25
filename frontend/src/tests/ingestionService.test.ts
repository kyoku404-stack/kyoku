/**
 * KEEP Enterprise Platform — Ingestion Service Unit Tests (Phase 2.1).
 *
 * Verifies that all 5 REST API service endpoints in ingestionService conform to:
 * - POST /api/v1/ingestion/start
 * - GET  /api/v1/ingestion/status/{id}
 * - GET  /api/v1/ingestion/jobs
 * - POST /api/v1/ingestion/retry/{id}
 * - GET  /api/v1/ingestion/statistics
 *
 * Specification: devdocs/p2/p2.1.txt Chapter 16 & docs/api/api-contract.md Section 8
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ingestionService } from '@/services/ingestionService';
import { apiClient } from '@/services/api';
import {
  ChunkingStrategy,
  EmbeddingModelProvider,
  IngestionJobStatus,
  type StartIngestionRequest,
} from '@/types/ingestion';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 2.1 Ingestion Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('startIngestion() enqueues job and returns StartIngestionResponseData', async () => {
    const mockPayload: StartIngestionRequest = {
      document_id: 'doc-uuid-1234',
      chunking_strategy: ChunkingStrategy.SEMANTIC_HEADING_AWARE,
      target_chunk_size: 512,
      chunk_overlap: 50,
      embedding_provider: EmbeddingModelProvider.OPENAI,
      embedding_model: 'text-embedding-3-small',
      force_ocr: false,
    };

    const mockResponse = {
      data: {
        success: true,
        message: 'Document ingestion job enqueued successfully.',
        data: {
          job_id: 'job-uuid-5678',
          document_id: 'doc-uuid-1234',
          status: IngestionJobStatus.PENDING,
          queue_name: 'ai_ingestion_queue',
          enqueued_at: '2026-10-25T10:00:00Z',
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

    const result = await ingestionService.startIngestion(mockPayload);

    expect(apiClient.post).toHaveBeenCalledWith('/ingestion/start', mockPayload);
    expect(result.success).toBe(true);
    expect(result.data.job_id).toBe('job-uuid-5678');
    expect(result.data.status).toBe(IngestionJobStatus.PENDING);
  });

  it('getIngestionStatus() queries status for a job or document ID', async () => {
    const mockJobId = 'job-uuid-5678';
    const mockResponse = {
      data: {
        success: true,
        message: 'Ingestion job status retrieved successfully.',
        data: {
          job_id: mockJobId,
          document_id: 'doc-uuid-1234',
          status: IngestionJobStatus.CHUNKING,
          progress_percent: 60.0,
          current_stage: 'CHUNKING',
          total_pages: 12,
          processed_pages: 12,
          chunks_generated: 45,
          embeddings_generated: 0,
          ocr_applied: false,
          retry_count: 0,
          error_message: null,
          started_at: '2026-10-25T10:00:00Z',
          completed_at: null,
          duration_seconds: 4.5,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

    const result = await ingestionService.getIngestionStatus(mockJobId);

    expect(apiClient.get).toHaveBeenCalledWith(`/ingestion/status/${mockJobId}`);
    expect(result.success).toBe(true);
    expect(result.data.current_stage).toBe('CHUNKING');
    expect(result.data.progress_percent).toBe(60.0);
    expect(result.data.chunks_generated).toBe(45);
  });

  it('listIngestionJobs() passes filters and returns paginated jobs', async () => {
    const mockParams = {
      page: 2,
      page_size: 10,
      status: IngestionJobStatus.COMPLETED,
      document_id: 'doc-uuid-1234',
    };

    const mockResponse = {
      data: {
        success: true,
        message: 'Ingestion jobs retrieved successfully.',
        data: {
          items: [
            {
              job_id: 'job-uuid-1',
              document_id: 'doc-uuid-1234',
              document_title: 'Quarterly Report.pdf',
              status: IngestionJobStatus.COMPLETED,
              chunks_generated: 32,
              duration_seconds: 3.8,
              created_at: '2026-10-25T09:30:00Z',
              completed_at: '2026-10-25T09:30:04Z',
            },
          ],
          total: 25,
          page: 2,
          page_size: 10,
          total_pages: 3,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

    const result = await ingestionService.listIngestionJobs(mockParams);

    expect(apiClient.get).toHaveBeenCalledWith('/ingestion/jobs', { params: mockParams });
    expect(result.success).toBe(true);
    expect(result.data.items).toHaveLength(1);
    expect(result.data.total).toBe(25);
    expect(result.data.page).toBe(2);
  });

  it('retryIngestionJob() re-enqueues a failed job', async () => {
    const mockJobId = 'job-uuid-failed-1';
    const mockResponse = {
      data: {
        success: true,
        message: 'Ingestion job re-enqueued for retry.',
        data: {
          job_id: mockJobId,
          status: IngestionJobStatus.RETRYING,
          retry_count: 1,
          enqueued_at: '2026-10-25T10:05:00Z',
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

    const result = await ingestionService.retryIngestionJob(mockJobId);

    expect(apiClient.post).toHaveBeenCalledWith(`/ingestion/retry/${mockJobId}`);
    expect(result.success).toBe(true);
    expect(result.data.status).toBe(IngestionJobStatus.RETRYING);
    expect(result.data.retry_count).toBe(1);
  });

  it('getIngestionStatistics() returns tenant-wide pipeline throughput metrics', async () => {
    const mockResponse = {
      data: {
        success: true,
        message: 'Ingestion statistics retrieved successfully.',
        data: {
          organization_id: 'org-uuid-8888',
          total_jobs: 150,
          completed_jobs: 142,
          failed_jobs: 3,
          pending_jobs: 5,
          total_chunks_indexed: 4200,
          average_duration_seconds: 3.45,
          average_throughput_pages_per_minute: 120.5,
          ocr_utilization_percent: 18.0,
          retry_success_rate_percent: 95.0,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

    const result = await ingestionService.getIngestionStatistics();

    expect(apiClient.get).toHaveBeenCalledWith('/ingestion/statistics');
    expect(result.success).toBe(true);
    expect(result.data.total_jobs).toBe(150);
    expect(result.data.total_chunks_indexed).toBe(4200);
    expect(result.data.average_throughput_pages_per_minute).toBe(120.5);
    expect(result.data.ocr_utilization_percent).toBe(18.0);
  });
});
