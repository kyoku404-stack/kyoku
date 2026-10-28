/**
 * KEEP Enterprise Platform — Plugin SDK & Developer Ecosystem Custom React Hook.
 *
 * Phase: 3.5
 * Specification: devdocs/p3/p3.5.txt & docs/API/api-contract.md (Section 17)
 * Role: Member 3 (Frontend & UI Lead)
 */

import { useCallback, useEffect, useState } from 'react';
import {
  pluginService,
  type MarketplaceQueryParams,
  type PluginListQueryParams,
  type PluginLogQueryParams,
} from '@/services/pluginService';
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

export function usePlugins() {
  const [installedPlugins, setInstalledPlugins] = useState<PluginItem[]>([]);
  const [marketplaceItems, setMarketplaceItems] = useState<PluginMarketplaceItem[]>([]);
  const [executionLogs, setExecutionLogs] = useState<PluginExecutionLog[]>([]);
  const [analytics, setAnalytics] = useState<PluginAnalytics | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginItem | null>(null);
  const [lastExecution, setLastExecution] = useState<PluginExecutionResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [executing, setExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ==========================================================================
  // Query Fetchers
  // ==========================================================================

  const fetchInstalledPlugins = useCallback(async (params?: PluginListQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const res = await pluginService.getInstalledPlugins(params);
      if (res.data) {
        setInstalledPlugins(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch installed plugins';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMarketplace = useCallback(async (params?: MarketplaceQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const res = await pluginService.getMarketplace(params);
      if (res.data) {
        setMarketplaceItems(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch marketplace catalog';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchExecutionLogs = useCallback(async (params?: PluginLogQueryParams) => {
    try {
      const res = await pluginService.getExecutionLogs(params);
      if (res.data) {
        setExecutionLogs(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch execution logs';
      setError(msg);
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await pluginService.getAnalytics();
      if (res.data) {
        setAnalytics(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch plugin analytics';
      setError(msg);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([
      fetchInstalledPlugins(),
      fetchMarketplace(),
      fetchExecutionLogs({ limit: 50 }),
      fetchAnalytics(),
    ]);
    setLoading(false);
  }, [fetchInstalledPlugins, fetchMarketplace, fetchExecutionLogs, fetchAnalytics]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  // ==========================================================================
  // Mutations & Actions
  // ==========================================================================

  const installPlugin = async (payload: PluginInstallPayload): Promise<PluginItem | null> => {
    try {
      setLoading(true);
      setError(null);
      const res = await pluginService.installPlugin(payload);
      if (res.data) {
        await refreshAll();
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to install plugin';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const uninstallPlugin = async (payload: PluginUninstallPayload): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);
      await pluginService.uninstallPlugin(payload);
      await refreshAll();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to uninstall plugin';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const enablePlugin = async (pluginId: string): Promise<PluginItem | null> => {
    try {
      setError(null);
      const res = await pluginService.enablePlugin(pluginId);
      if (res.data) {
        setInstalledPlugins((prev) =>
          prev.map((p) => (p.plugin_id === pluginId ? { ...p, is_enabled: true, status: 'ACTIVE' } : p))
        );
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to activate plugin';
      setError(msg);
      throw err;
    }
  };

  const disablePlugin = async (pluginId: string): Promise<PluginItem | null> => {
    try {
      setError(null);
      const res = await pluginService.disablePlugin(pluginId);
      if (res.data) {
        setInstalledPlugins((prev) =>
          prev.map((p) => (p.plugin_id === pluginId ? { ...p, is_enabled: false, status: 'DISABLED' } : p))
        );
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to deactivate plugin';
      setError(msg);
      throw err;
    }
  };

  const updatePluginVersion = async (payload: PluginUpdatePayload): Promise<PluginItem | null> => {
    try {
      setLoading(true);
      setError(null);
      const res = await pluginService.updatePluginVersion(payload);
      if (res.data) {
        await refreshAll();
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update plugin version';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updatePluginConfig = async (
    pluginId: string,
    payload: PluginConfigUpdatePayload
  ): Promise<PluginItem | null> => {
    try {
      setError(null);
      const res = await pluginService.updatePluginConfig(pluginId, payload);
      if (res.data) {
        setInstalledPlugins((prev) =>
          prev.map((p) => (p.plugin_id === pluginId ? { ...p, configuration: res.data.configuration } : p))
        );
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update plugin configuration';
      setError(msg);
      throw err;
    }
  };

  const executePlugin = async (
    pluginId: string,
    payload: PluginExecutePayload
  ): Promise<PluginExecutionResponse | null> => {
    try {
      setExecuting(true);
      setError(null);
      const res = await pluginService.executePlugin(pluginId, payload);
      if (res.data) {
        setLastExecution(res.data);
        await Promise.all([fetchExecutionLogs({ limit: 50 }), fetchAnalytics()]);
        return res.data;
      }
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to execute plugin action';
      setError(msg);
      throw err;
    } finally {
      setExecuting(false);
    }
  };

  const publishPlugin = async (payload: PluginPublishPayload): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);
      await pluginService.publishPlugin(payload);
      await fetchMarketplace();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to publish plugin';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    installedPlugins,
    marketplaceItems,
    executionLogs,
    analytics,
    selectedPlugin,
    setSelectedPlugin,
    lastExecution,
    loading,
    executing,
    error,
    fetchInstalledPlugins,
    fetchMarketplace,
    fetchExecutionLogs,
    fetchAnalytics,
    refreshAll,
    installPlugin,
    uninstallPlugin,
    enablePlugin,
    disablePlugin,
    updatePluginVersion,
    updatePluginConfig,
    executePlugin,
    publishPlugin,
  };
}
