/**
 * KEEP Enterprise Platform — Phase 4.11 Proactive Intelligence API Service.
 */

import { apiClient } from './api';
import type {
  ApiEnvelope,
  DetectionRunRecord,
  EvidenceReference,
  FeedbackType,
  InsightCategory,
  InsightStatus,
  IntelligenceInsight,
  OperationalMetrics,
  ScanRequest,
} from '@/types/proactiveIntelligence';

export const proactiveIntelligenceService = {
  async listInsights(params?: {
    category?: InsightCategory;
    status?: InsightStatus;
    min_priority?: number;
    limit?: number;
  }): Promise<ApiEnvelope<IntelligenceInsight[]>> {
    const res = await apiClient.get<ApiEnvelope<IntelligenceInsight[]>>('/intelligence/insights', {
      params,
    });
    return res.data;
  },

  async getInsight(insightId: string): Promise<ApiEnvelope<IntelligenceInsight>> {
    const res = await apiClient.get<ApiEnvelope<IntelligenceInsight>>(
      `/intelligence/insights/${insightId}`
    );
    return res.data;
  },

  async getEvidence(insightId: string): Promise<ApiEnvelope<EvidenceReference[]>> {
    const res = await apiClient.get<ApiEnvelope<EvidenceReference[]>>(
      `/intelligence/insights/${insightId}/evidence`
    );
    return res.data;
  },

  async submitFeedback(
    insightId: string,
    feedback: FeedbackType,
    comment?: string
  ): Promise<ApiEnvelope<Record<string, unknown>>> {
    const res = await apiClient.post<ApiEnvelope<Record<string, unknown>>>(
      `/intelligence/insights/${insightId}/feedback`,
      { feedback, comment }
    );
    return res.data;
  },

  async dismissInsight(
    insightId: string,
    scope: 'user' | 'organization' = 'user',
    reason = 'Dismissed by user'
  ): Promise<ApiEnvelope<IntelligenceInsight>> {
    const res = await apiClient.post<ApiEnvelope<IntelligenceInsight>>(
      `/intelligence/insights/${insightId}/dismiss`,
      { scope, reason }
    );
    return res.data;
  },

  async resolveInsight(
    insightId: string,
    resolutionNote = 'Resolved'
  ): Promise<ApiEnvelope<IntelligenceInsight>> {
    const res = await apiClient.post<ApiEnvelope<IntelligenceInsight>>(
      `/intelligence/insights/${insightId}/resolve`,
      { resolution_note: resolutionNote }
    );
    return res.data;
  },

  async investigateInsight(
    insightId: string,
    workflowId = 'knowledge_analysis',
    notes?: string
  ): Promise<ApiEnvelope<IntelligenceInsight>> {
    const res = await apiClient.post<ApiEnvelope<IntelligenceInsight>>(
      `/intelligence/insights/${insightId}/investigate`,
      { workflow_id: workflowId, notes }
    );
    return res.data;
  },

  async requestScan(payload: ScanRequest): Promise<ApiEnvelope<DetectionRunRecord>> {
    const res = await apiClient.post<ApiEnvelope<DetectionRunRecord>>(
      '/intelligence/scans',
      payload
    );
    return res.data;
  },

  async getMetrics(): Promise<ApiEnvelope<OperationalMetrics>> {
    const res = await apiClient.get<ApiEnvelope<OperationalMetrics>>('/intelligence/metrics');
    return res.data;
  },
};
