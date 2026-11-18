/**
 * KEEP Enterprise Platform — Phase 4.5 Research Agents API Client Service.
 *
 * Consumes KEEP's Phase 4.5 Research endpoints using relative paths over `apiClient`:
 * - `POST /research`
 * - `GET  /research`
 * - `GET  /research/{research_id}`
 * - `GET  /research/{research_id}/report`
 * - `GET  /research/{research_id}/evidence`
 * - `POST /research/{research_id}/cancel`
 */

import { apiClient } from './api';
import type {
  ResearchEvidenceResponse,
  ResearchLaunchResponse,
  ResearchListResponse,
  ResearchReportResponse,
  ResearchRunDetailResponse,
  ResearchStatus,
  StartResearchRequest,
} from '@/types/research';

export const researchService = {
  /**
   * Starts a synchronous or asynchronous evidence-first research investigation.
   */
  async startResearch(
    payload: StartResearchRequest,
    idempotencyKey?: string
  ): Promise<ResearchLaunchResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey && idempotencyKey.trim()) {
      headers['Idempotency-Key'] = idempotencyKey.trim();
    }
    const response = await apiClient.post<ResearchLaunchResponse>(
      '/research',
      payload,
      Object.keys(headers).length > 0 ? { headers } : undefined
    );
    return response.data;
  },

  /**
   * Lists tenant-scoped research investigations with optional status filtering.
   */
  async listRuns(params?: {
    status?: ResearchStatus;
    limit?: number;
  }): Promise<ResearchListResponse> {
    const response = await apiClient.get<ResearchListResponse>('/research', { params });
    return response.data;
  },

  /**
   * Retrieves investigation status, latency telemetry, and append-only audit events.
   */
  async getRun(researchId: string): Promise<ResearchRunDetailResponse> {
    const response = await apiClient.get<ResearchRunDetailResponse>(
      `/research/${encodeURIComponent(researchId)}`
    );
    return response.data;
  },

  /**
   * Retrieves the re-authorized, citation-backed ResearchReport.
   */
  async getReport(researchId: string): Promise<ResearchReportResponse> {
    const response = await apiClient.get<ResearchReportResponse>(
      `/research/${encodeURIComponent(researchId)}/report`
    );
    return response.data;
  },

  /**
   * Retrieves re-authorized evidence passages and source provenance metadata.
   */
  async getEvidence(researchId: string): Promise<ResearchEvidenceResponse> {
    const response = await apiClient.get<ResearchEvidenceResponse>(
      `/research/${encodeURIComponent(researchId)}/evidence`
    );
    return response.data;
  },

  /**
   * Cooperatively cancels a pending or running research investigation.
   */
  async cancelRun(researchId: string): Promise<ResearchRunDetailResponse> {
    const response = await apiClient.post<ResearchRunDetailResponse>(
      `/research/${encodeURIComponent(researchId)}/cancel`
    );
    return response.data;
  },
};
