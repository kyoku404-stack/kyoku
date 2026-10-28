/**
 * KEEP Enterprise Platform — Plugin SDK & Developer Ecosystem API Client Service.
 *
 * Phase: 3.5
 * Specification: devdocs/p3/p3.5.txt & docs/API/api-contract.md (Section 17)
 * Role: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  PluginAnalytics,
  PluginConfigUpdatePayload,
  PluginExecutePayload,
  PluginExecutionLog,
  PluginExecutionResponse,
  PluginInstallPayload,
  PluginItem,
  PluginMarketplaceItem,
  PluginPublishPayload,
  PluginUninstallPayload,
  PluginUpdatePayload,
} from '@/types/plugin';

export interface MarketplaceQueryParams {
  search?: string;
  category?: string;
  verified_only?: boolean;
}

export interface PluginListQueryParams {
  category?: string;
  status?: string;
}

export interface PluginLogQueryParams {
  plugin_id?: string;
  status?: string;
  limit?: number;
}

export const pluginService = {
  /**
   * Browse the marketplace catalog with tenant installation status.
   */
  async getMarketplace(params?: MarketplaceQueryParams): Promise<ApiResponse<PluginMarketplaceItem[]>> {
    const response = await apiClient.get<ApiResponse<PluginMarketplaceItem[]>>('/api/v1/plugins/marketplace', {
      params,
    });
    return response.data;
  },

  /**
   * Publish a new extension manifest to the global marketplace.
   */
  async publishPlugin(payload: PluginPublishPayload): Promise<ApiResponse<{ id: string; plugin_id: string; name: string; status: string }>> {
    const response = await apiClient.post<ApiResponse<{ id: string; plugin_id: string; name: string; status: string }>>(
      '/api/v1/plugins/marketplace/publish',
      payload
    );
    return response.data;
  },

  /**
   * Install a plugin for the tenant organization.
   */
  async installPlugin(payload: PluginInstallPayload): Promise<ApiResponse<PluginItem>> {
    const response = await apiClient.post<ApiResponse<PluginItem>>('/api/v1/plugins/install', payload);
    return response.data;
  },

  /**
   * Query all installed plugins configured for the caller's organization.
   */
  async getInstalledPlugins(params?: PluginListQueryParams): Promise<ApiResponse<PluginItem[]>> {
    const response = await apiClient.get<ApiResponse<PluginItem[]>>('/api/v1/plugins/list', {
      params,
    });
    return response.data;
  },

  /**
   * Retrieve full configuration and details for a specific plugin.
   */
  async getPluginDetails(pluginId: string): Promise<ApiResponse<PluginItem>> {
    const response = await apiClient.get<ApiResponse<PluginItem>>(`/api/v1/plugins/${pluginId}`);
    return response.data;
  },

  /**
   * Update runtime configuration settings for an installed plugin.
   */
  async updatePluginConfig(pluginId: string, payload: PluginConfigUpdatePayload): Promise<ApiResponse<PluginItem>> {
    const response = await apiClient.post<ApiResponse<PluginItem>>(`/api/v1/plugins/${pluginId}/config`, payload);
    return response.data;
  },

  /**
   * Activate an installed plugin.
   */
  async enablePlugin(pluginId: string): Promise<ApiResponse<PluginItem>> {
    const response = await apiClient.post<ApiResponse<PluginItem>>('/api/v1/plugins/enable', {
      plugin_id: pluginId,
    });
    return response.data;
  },

  /**
   * Deactivate an installed plugin.
   */
  async disablePlugin(pluginId: string): Promise<ApiResponse<PluginItem>> {
    const response = await apiClient.post<ApiResponse<PluginItem>>('/api/v1/plugins/disable', {
      plugin_id: pluginId,
    });
    return response.data;
  },

  /**
   * Upgrade or downgrade installed plugin version.
   */
  async updatePluginVersion(payload: PluginUpdatePayload): Promise<ApiResponse<PluginItem>> {
    const response = await apiClient.post<ApiResponse<PluginItem>>('/api/v1/plugins/update', payload);
    return response.data;
  },

  /**
   * Execute an action inside a sandboxed plugin runtime.
   */
  async executePlugin(pluginId: string, payload: PluginExecutePayload): Promise<ApiResponse<PluginExecutionResponse>> {
    const response = await apiClient.post<ApiResponse<PluginExecutionResponse>>(
      `/api/v1/plugins/${pluginId}/execute`,
      payload
    );
    return response.data;
  },

  /**
   * Query plugin execution telemetry history and audit logs.
   */
  async getExecutionLogs(params?: PluginLogQueryParams): Promise<ApiResponse<PluginExecutionLog[]>> {
    const response = await apiClient.get<ApiResponse<PluginExecutionLog[]>>('/api/v1/plugins/logs', {
      params,
    });
    return response.data;
  },

  /**
   * Retrieve operational KPIs and performance telemetry.
   */
  async getAnalytics(): Promise<ApiResponse<PluginAnalytics>> {
    const response = await apiClient.get<ApiResponse<PluginAnalytics>>('/api/v1/plugins/analytics');
    return response.data;
  },

  /**
   * Remove a plugin installation from organization workspace.
   */
  async uninstallPlugin(payload: PluginUninstallPayload): Promise<ApiResponse<{ success: boolean; message: string }>> {
    const response = await apiClient.post<ApiResponse<{ success: boolean; message: string }>>(
      '/api/v1/plugins/uninstall',
      payload
    );
    return response.data;
  },
};
