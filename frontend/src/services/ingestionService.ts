/**
 * KEEP Enterprise Platform — AI Knowledge Ingestion Pipeline Service Client (Phase 2.1).
 *
 * Implements REST client methods for all 5 Phase 2.1 ingestion endpoints:
 * - POST /api/v1/ingestion/start (Trigger asynchronous processing)
 * - GET  /api/v1/ingestion/status/{id} (Poll real-time job or document progress)
 * - GET  /api/v1/ingestion/jobs (List tenant ingestion runs with filters)
 * - POST /api/v1/ingestion/retry/{id} (Retry dead-lettered/failed jobs)
 * - GET  /api/v1/ingestion/statistics (Retrieve tenant-wide pipeline throughput & metrics)
 *
 * Specification: docs/api/api-contract.md Section 8 & devdocs/p2/p2.1.txt Chapter 16
 * Author: Member 3 (Frontend Lead)
 */

import { apiClient } from './api';
import type {
  StartIngestionRequest,
  StartIngestionApiResponse,
  IngestionStatusApiResponse,
  IngestionJobsApiResponse,
  IngestionRetryApiResponse,
  IngestionStatisticsApiResponse,
  IngestionJobListParams,
} from '@/types/ingestion';

export const ingestionService = {
  /**
   * Enqueue a document for asynchronous parsing, OCR, chunking, and vector embedding.
   * POST /api/v1/ingestion/start → 202 Accepted
   */
  async startIngestion(payload: StartIngestionRequest): Promise<StartIngestionApiResponse> {
    const response = await apiClient.post<StartIngestionApiResponse>(
      '/ingestion/start',
      payload
    );
    return response.data;
  },

  /**
   * Retrieve real-time pipeline status, progress percentage, active stage, and chunk metrics.
   * Can be queried by either ingestion job_id or target document_id.
   * GET /api/v1/ingestion/status/{id} → 200 OK
   */
  async getIngestionStatus(id: string): Promise<IngestionStatusApiResponse> {
    const response = await apiClient.get<IngestionStatusApiResponse>(
      `/ingestion/status/${id}`
    );
    return response.data;
  },

  /**
   * List historical and active ingestion jobs for the tenant with optional status and document filters.
   * GET /api/v1/ingestion/jobs → 200 OK (Paginated)
   */
  async listIngestionJobs(params?: IngestionJobListParams): Promise<IngestionJobsApiResponse> {
    const response = await apiClient.get<IngestionJobsApiResponse>(
      '/ingestion/jobs',
      { params }
    );
    return response.data;
  },

  /**
   * Re-enqueue a failed or dead-lettered ingestion job for execution.
   * POST /api/v1/ingestion/retry/{id} → 200 OK
   */
  async retryIngestionJob(id: string): Promise<IngestionRetryApiResponse> {
    const response = await apiClient.post<IngestionRetryApiResponse>(
      `/ingestion/retry/${id}`
    );
    return response.data;
  },

  /**
   * Retrieve tenant-wide operational metrics (total jobs, chunks indexed, duration, throughput, OCR utilization).
   * GET /api/v1/ingestion/statistics → 200 OK
   */
  async getIngestionStatistics(): Promise<IngestionStatisticsApiResponse> {
    const response = await apiClient.get<IngestionStatisticsApiResponse>(
      '/ingestion/statistics'
    );
    return response.data;
  },
};

export default ingestionService;
