/**
 * KEEP Enterprise Platform — Production Infrastructure & Operations API Client Service.
 *
 * Phase: 3.6
 * Specification: devdocs/p3/p3.6.txt (Chapter 16) & docs/api/api-contract.md (Section 18)
 * Role: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  CacheFlushData,
  CacheFlushRequest,
  CreateBackupData,
  CreateBackupRequest,
  DeployTriggerData,
  DeployTriggerRequest,
  MicroserviceStatusData,
  SystemBackupsData,
  SystemHealthData,
  SystemLogEntryData,
  SystemMetricsData,
  SystemVersionData,
} from '@/types/system';

export interface SystemLogsQueryParams {
  service_name?: string;
  severity?: string;
  limit?: number;
  query?: string;
}

export const systemService = {
  /**
   * Retrieves aggregated platform health probe and subsystem diagnostics.
   */
  async getHealth(): Promise<ApiResponse<SystemHealthData>> {
    const response = await apiClient.get<ApiResponse<SystemHealthData>>('/api/v1/system/health');
    return response.data;
  },

  /**
   * Retrieves real-time hardware, network, and application telemetry metrics.
   */
  async getMetrics(): Promise<ApiResponse<SystemMetricsData>> {
    const response = await apiClient.get<ApiResponse<SystemMetricsData>>('/api/v1/system/metrics');
    return response.data;
  },

  /**
   * Queries centralized operational and diagnostic logs.
   */
  async getLogs(params?: SystemLogsQueryParams): Promise<ApiResponse<SystemLogEntryData[]>> {
    const response = await apiClient.get<ApiResponse<SystemLogEntryData[]>>('/api/v1/system/logs', {
      params,
    });
    return response.data;
  },

  /**
   * Dispatches a rolling, blue-green, or canary service deployment.
   */
  async triggerDeploy(payload: DeployTriggerRequest): Promise<ApiResponse<DeployTriggerData>> {
    const response = await apiClient.post<ApiResponse<DeployTriggerData>>('/api/v1/system/deploy', payload);
    return response.data;
  },

  /**
   * Retrieves platform release version and environment specifications.
   */
  async getVersion(): Promise<ApiResponse<SystemVersionData>> {
    const response = await apiClient.get<ApiResponse<SystemVersionData>>('/api/v1/system/version');
    return response.data;
  },

  /**
   * Retrieves microservices operational state matrix and replica counts.
   */
  async getStatus(): Promise<ApiResponse<MicroserviceStatusData[]>> {
    const response = await apiClient.get<ApiResponse<MicroserviceStatusData[]>>('/api/v1/system/status');
    return response.data;
  },

  /**
   * Retrieves disaster recovery backup catalog and RPO/RTO metrics.
   */
  async getBackups(): Promise<ApiResponse<SystemBackupsData>> {
    const response = await apiClient.get<ApiResponse<SystemBackupsData>>('/api/v1/system/backups');
    return response.data;
  },

  /**
   * Creates an immediate point-in-time backup snapshot.
   */
  async createBackup(payload: CreateBackupRequest): Promise<ApiResponse<CreateBackupData>> {
    const response = await apiClient.post<ApiResponse<CreateBackupData>>('/api/v1/system/backups/create', payload);
    return response.data;
  },

  /**
   * Flushes designated Redis cache namespaces.
   */
  async flushCache(payload: CacheFlushRequest): Promise<ApiResponse<CacheFlushData>> {
    const response = await apiClient.post<ApiResponse<CacheFlushData>>('/api/v1/system/cache/flush', payload);
    return response.data;
  },
};

