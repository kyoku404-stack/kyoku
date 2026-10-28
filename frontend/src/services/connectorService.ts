/**
 * Phase 3.1 Enterprise Integrations & Connector Framework API Client Service.
 * Implements communication with all 7 Phase 3.1 REST endpoints:
 * - POST /api/v1/connectors/register
 * - POST /api/v1/connectors/authenticate
 * - GET /api/v1/connectors/list
 * - POST /api/v1/connectors/sync
 * - GET /api/v1/connectors/status/{id}
 * - DELETE /api/v1/connectors/remove/{id}
 * - GET /api/v1/connectors/logs
 *
 * Specification: docs/api/api-contract.md Section 13 & devdocs/p3/p3.1.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  ConnectorAuthenticateRequest,
  ConnectorAuthenticateResponse,
  ConnectorListResponse,
  ConnectorLogsResponse,
  ConnectorRegisterRequest,
  ConnectorRegisterResponse,
  ConnectorRemoveResponse,
  ConnectorStatusResponse,
  ConnectorSyncRequest,
  ConnectorSyncResponse,
} from '@/types/connector';

export const connectorService = {
  /**
   * Registers a new external enterprise platform connector.
   * POST /api/v1/connectors/register
   */
  async register(
    payload: ConnectorRegisterRequest
  ): Promise<ApiResponse<ConnectorRegisterResponse>> {
    const response = await apiClient.post<ApiResponse<ConnectorRegisterResponse>>(
      '/connectors/register',
      payload
    );
    return response.data;
  },

  /**
   * Provides credentials or triggers OAuth authentication for a connector.
   * POST /api/v1/connectors/authenticate
   */
  async authenticate(
    payload: ConnectorAuthenticateRequest
  ): Promise<ApiResponse<ConnectorAuthenticateResponse>> {
    const response = await apiClient.post<ApiResponse<ConnectorAuthenticateResponse>>(
      '/connectors/authenticate',
      payload
    );
    return response.data;
  },

  /**
   * Retrieves all configured connectors for the tenant.
   * GET /api/v1/connectors/list
   */
  async list(
    platformCategory?: string,
    statusFilter?: string
  ): Promise<ApiResponse<ConnectorListResponse>> {
    const params = new URLSearchParams();
    if (platformCategory && platformCategory !== 'ALL') {
      params.append('platform_category', platformCategory);
    }
    if (statusFilter && statusFilter !== 'ALL') {
      params.append('status', statusFilter);
    }

    const response = await apiClient.get<ApiResponse<ConnectorListResponse>>(
      `/connectors/list${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Triggers full or incremental synchronization on a connector.
   * POST /api/v1/connectors/sync
   */
  async sync(
    payload: ConnectorSyncRequest
  ): Promise<ApiResponse<ConnectorSyncResponse>> {
    const response = await apiClient.post<ApiResponse<ConnectorSyncResponse>>(
      '/connectors/sync',
      payload
    );
    return response.data;
  },

  /**
   * Retrieves real-time health telemetry and operational status for a connector.
   * GET /api/v1/connectors/status/{id}
   */
  async getStatus(id: string): Promise<ApiResponse<ConnectorStatusResponse>> {
    const response = await apiClient.get<ApiResponse<ConnectorStatusResponse>>(
      `/connectors/status/${id}`
    );
    return response.data;
  },

  /**
   * Removes and disconnects a registered connector instance.
   * DELETE /api/v1/connectors/remove/{id}
   */
  async remove(id: string): Promise<ApiResponse<ConnectorRemoveResponse>> {
    const response = await apiClient.delete<ApiResponse<ConnectorRemoveResponse>>(
      `/connectors/remove/${id}`
    );
    return response.data;
  },

  /**
   * Retrieves synchronization audit execution logs.
   * GET /api/v1/connectors/logs
   */
  async getLogs(
    connectorId?: string,
    limit: number = 50,
    statusFilter?: string
  ): Promise<ApiResponse<ConnectorLogsResponse>> {
    const params = new URLSearchParams();
    if (connectorId) {
      params.append('connector_id', connectorId);
    }
    if (limit) {
      params.append('limit', limit.toString());
    }
    if (statusFilter && statusFilter !== 'ALL') {
      params.append('status', statusFilter);
    }

    const response = await apiClient.get<ApiResponse<ConnectorLogsResponse>>(
      `/connectors/logs${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },
};
