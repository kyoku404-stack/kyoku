/**
 * KEEP Enterprise Platform — Analytics Service Client.
 * Connects to /api/v1/analytics endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  AnalyticsSummaryResponse,
  UsageMetricsResponse,
} from '@/types/analytics';

export const analyticsService = {
  /**
   * Retrieves operational summary metrics.
   * GET /api/v1/analytics/summary
   */
  async getSummary(): Promise<ApiResponse<AnalyticsSummaryResponse>> {
    const response = await apiClient.get<ApiResponse<AnalyticsSummaryResponse>>(
      '/analytics/summary'
    );
    return response.data;
  },

  /**
   * Retrieves daily query volume and latency statistics.
   * GET /api/v1/analytics/usage
   */
  async getUsage(): Promise<ApiResponse<UsageMetricsResponse>> {
    const response = await apiClient.get<ApiResponse<UsageMetricsResponse>>(
      '/analytics/usage'
    );
    return response.data;
  },
};

export default analyticsService;
