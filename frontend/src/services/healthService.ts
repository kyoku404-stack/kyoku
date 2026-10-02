import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  DetailedHealthResponse,
  HealthCheckResponse,
  RootDiscoveryResponse,
} from '@/types/health';
import axios from 'axios';

/**
 * Service to monitor backend health and platform readiness.
 */
export const healthService = {
  /**
   * Fetches backend health check (/api/v1/health)
   */
  async checkHealth(): Promise<HealthCheckResponse> {
    const response = await apiClient.get<HealthCheckResponse>('/health');
    return response.data;
  },

  /**
   * Fetches detailed diagnostic health check (/api/v1/health/details)
   */
  async getDetailedHealth(): Promise<ApiResponse<DetailedHealthResponse>> {
    const response = await apiClient.get<ApiResponse<DetailedHealthResponse>>('/health/details');
    return response.data;
  },

  /**
   * Fetches root discovery endpoint (/)
   */
  async getRootDiscovery(): Promise<RootDiscoveryResponse> {
    // Root endpoint is outside /api/v1
    const rootUrl = (apiClient.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '');
    const response = await axios.get<RootDiscoveryResponse>(rootUrl || '/');
    return response.data;
  },
};

export default healthService;
