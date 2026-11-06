/**
 * KEEP Enterprise Platform — Phase 3.7 Production Release & Security Audit API Client Service.
 *
 * Specification: devdocs/p3/p3.7.txt Section 19 & docs/api/api-contract.md
 * Author: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type {
  ReleaseDeployRequest,
  ReleaseDeployResponse,
  ReleaseHistoryResponse,
  SecurityAuditResponse,
  SystemReadinessResponse,
} from '@/types/release';

export const releaseService = {
  /**
   * Evaluates platform pre-flight readiness gate across all 7 core subsystems.
   */
  async getReadiness(targetVersion: string = '1.0.0'): Promise<SystemReadinessResponse> {
    const response = await apiClient.get<SystemReadinessResponse>('/api/v1/system/readiness', {
      params: { target_version: targetVersion },
    });
    return response.data;
  },

  /**
   * Dispatches a production release deployment when all pre-flight gates pass.
   */
  async triggerRelease(payload: ReleaseDeployRequest): Promise<ReleaseDeployResponse> {
    const response = await apiClient.post<ReleaseDeployResponse>('/api/v1/system/release', payload);
    return response.data;
  },

  /**
   * Retrieves catalog of historical production releases ordered newest first.
   */
  async getReleaseHistory(limit: number = 50): Promise<ReleaseHistoryResponse> {
    const response = await apiClient.get<ReleaseHistoryResponse>('/api/v1/system/releases', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Executes automated OWASP Top 10 & LLM Top 10 enterprise security audit.
   */
  async getSecurityAudit(): Promise<SecurityAuditResponse> {
    const response = await apiClient.get<SecurityAuditResponse>('/api/v1/system/security/audit');
    return response.data;
  },
};

