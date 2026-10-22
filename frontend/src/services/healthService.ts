import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  DetailedHealthResponse,
  HealthCheckResponse,
  RootDiscoveryResponse,
  CompositeHealthResponse,
} from '@/types/health';
import axios from 'axios';
import { observabilityService } from './observabilityService';

/**
 * Service to monitor backend health and platform readiness.
 */
export const healthService = {
  /**
   * Fetches backend health check (/api/v1/health or root /health)
   */
  async checkHealth(): Promise<HealthCheckResponse> {
    try {
      const response = await apiClient.get<HealthCheckResponse>('/health');
      return response.data;
    } catch {
      return observabilityService.getCompositeHealth();
    }
  },

  /**
   * Fetches composite multi-tier health probe
   */
  async getCompositeHealth(): Promise<CompositeHealthResponse> {
    return observabilityService.getCompositeHealth();
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

export { observabilityService };
export default healthService;

