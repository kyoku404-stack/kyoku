/**
 * Phase 3.5 Plugin SDK & Extension Framework API Client Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { pluginService } from '@/services/pluginService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 3.5 Plugin Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getMarketplace() queries /api/v1/plugins/marketplace', async () => {
    const mockCatalog = [
      {
        id: 'claude-ai',
        plugin_id: 'ai-anthropic-claude',
        name: 'Anthropic Claude',
        category: 'AI',
        rating: 4.9,
      },
    ];
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockCatalog },
    });

    const res = await pluginService.getMarketplace({ search: 'claude', verified_only: true });

    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plugins/marketplace', {
      params: { search: 'claude', verified_only: true },
    });
    expect(res.data).toEqual(mockCatalog);
  });

  it('installPlugin() posts payload to /api/v1/plugins/install', async () => {
    const mockInstalled = {
      id: 'inst-1',
      plugin_id: 'sap-s4hana-connector',
      name: 'SAP Connector',
      is_enabled: true,
      status: 'ACTIVE',
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Installed', data: mockInstalled },
    });

    const res = await pluginService.installPlugin({
      plugin_id: 'sap-s4hana-connector',
      approved_permissions: ['READ_DOCUMENTS'],
      configuration: { endpoint: 'https://sap.acme.com' },
    });

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plugins/install', {
      plugin_id: 'sap-s4hana-connector',
      approved_permissions: ['READ_DOCUMENTS'],
      configuration: { endpoint: 'https://sap.acme.com' },
    });
    expect(res.data).toEqual(mockInstalled);
  });

  it('getInstalledPlugins() passes category to /api/v1/plugins/list', async () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: [] },
    });

    await pluginService.getInstalledPlugins({ category: 'AI' });
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plugins/list', {
      params: { category: 'AI' },
    });
  });

  it('enablePlugin() and disablePlugin() post to correct activation endpoints', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { success: true, message: 'Updated', data: { plugin_id: 'test-p' } },
    });

    await pluginService.enablePlugin('test-p');
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plugins/enable', { plugin_id: 'test-p' });

    await pluginService.disablePlugin('test-p');
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plugins/disable', { plugin_id: 'test-p' });
  });

  it('executePlugin() calls sandboxed action execution endpoint', async () => {
    const mockResult = {
      execution_id: 'exec-1',
      plugin_id: 'ai-anthropic-claude',
      action: 'generate',
      status: 'SUCCESS',
      duration_ms: 124.5,
      result: { completion: 'Done' },
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Executed', data: mockResult },
    });

    const res = await pluginService.executePlugin('ai-anthropic-claude', {
      action: 'generate',
      parameters: { prompt: 'Hello world' },
    });

    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plugins/ai-anthropic-claude/execute', {
      action: 'generate',
      parameters: { prompt: 'Hello world' },
    });
    expect(res.data).toEqual(mockResult);
  });

  it('getAnalytics() retrieves operational KPIs', async () => {
    const mockAnalytics = {
      total_installed_plugins: 3,
      active_plugins: 2,
      total_executions: 450,
      avg_latency_ms: 62.4,
      error_rate: 1.2,
      plugins_by_category: { AI: 2, INTEGRATION: 1 },
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'OK', data: mockAnalytics },
    });

    const res = await pluginService.getAnalytics();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plugins/analytics');
    expect(res.data).toEqual(mockAnalytics);
  });

  it('uninstallPlugin() calls uninstall endpoint', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Uninstalled', data: { success: true, message: 'Removed' } },
    });

    const res = await pluginService.uninstallPlugin({ plugin_id: 'test-p', purge_data: true });
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plugins/uninstall', {
      plugin_id: 'test-p',
      purge_data: true,
    });
    expect(res.data.success).toBe(true);
  });
});
