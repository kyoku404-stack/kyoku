/**
 * Phase 2.5 Enterprise Intelligence & Predictive Analytics API Client Service.
 * Implements communication with all 7 Phase 2.5 REST endpoints:
 * - GET /api/v1/analytics/dashboard
 * - GET /api/v1/analytics/kpis
 * - GET /api/v1/analytics/trends
 * - GET /api/v1/analytics/predictions
 * - GET /api/v1/analytics/anomalies
 * - GET /api/v1/analytics/recommendations
 * - GET /api/v1/analytics/knowledge-health
 *
 * Specification: docs/api/api-contract.md Section 12 & devdocs/p2/p2.5.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  ExecutiveDashboardResponse,
  KPIsResponse,
  TrendAnalysisResponse,
  PredictionsResponse,
  AnomaliesResponse,
  RecommendationsResponse,
  KnowledgeHealthResponse,
} from '@/types/intelligence';

export const intelligenceService = {
  /**
   * Retrieves the consolidated executive briefing and intelligence overview.
   * GET /api/v1/analytics/dashboard
   */
  async getExecutiveDashboard(): Promise<ApiResponse<ExecutiveDashboardResponse>> {
    const response = await apiClient.get<ApiResponse<ExecutiveDashboardResponse>>(
      '/analytics/dashboard'
    );
    return response.data;
  },

  /**
   * Retrieves core real-time operational indicators (KPIs).
   * GET /api/v1/analytics/kpis
   */
  async getKPIs(): Promise<ApiResponse<KPIsResponse>> {
    const response = await apiClient.get<ApiResponse<KPIsResponse>>(
      '/analytics/kpis'
    );
    return response.data;
  },

  /**
   * Retrieves historical multi-series trend analysis.
   * GET /api/v1/analytics/trends
   */
  async getTrends(
    days: number = 30,
    metric: string = 'all'
  ): Promise<ApiResponse<TrendAnalysisResponse>> {
    const response = await apiClient.get<ApiResponse<TrendAnalysisResponse>>(
      '/analytics/trends',
      {
        params: { days, metric },
      }
    );
    return response.data;
  },

  /**
   * Retrieves statistical forecasts and storage runway projections.
   * GET /api/v1/analytics/predictions
   */
  async getPredictions(
    horizonDays: number = 30
  ): Promise<ApiResponse<PredictionsResponse>> {
    const response = await apiClient.get<ApiResponse<PredictionsResponse>>(
      '/analytics/predictions',
      {
        params: { horizon_days: horizonDays },
      }
    );
    return response.data;
  },

  /**
   * Retrieves active and resolved operational anomalies.
   * GET /api/v1/analytics/anomalies
   */
  async getAnomalies(): Promise<ApiResponse<AnomaliesResponse>> {
    const response = await apiClient.get<ApiResponse<AnomaliesResponse>>(
      '/analytics/anomalies'
    );
    return response.data;
  },

  /**
   * Retrieves prioritized strategic AI recommendations.
   * GET /api/v1/analytics/recommendations
   */
  async getRecommendations(
    status: string = 'ACTIVE'
  ): Promise<ApiResponse<RecommendationsResponse>> {
    const response = await apiClient.get<ApiResponse<RecommendationsResponse>>(
      '/analytics/recommendations',
      {
        params: { status },
      }
    );
    return response.data;
  },

  /**
   * Computes multi-dimensional Knowledge Health Score breakdown and gap analysis.
   * GET /api/v1/analytics/knowledge-health
   */
  async getKnowledgeHealth(): Promise<ApiResponse<KnowledgeHealthResponse>> {
    const response = await apiClient.get<ApiResponse<KnowledgeHealthResponse>>(
      '/analytics/knowledge-health'
    );
    return response.data;
  },
};
