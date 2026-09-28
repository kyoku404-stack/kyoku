import { apiClient } from './api';
import type { HealthCheckResponse, RootDiscoveryResponse } from '@/types/health';
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
   * Fetches root discovery endpoint (/)
   */
  async getRootDiscovery(): Promise<RootDiscoveryResponse> {
    // Root endpoint is outside /api/v1
    const rootUrl = (apiClient.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '');
    const response = await axios.get<RootDiscoveryResponse>(rootUrl || '/');
    return response.data;
  },
};
