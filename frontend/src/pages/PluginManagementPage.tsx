/**
 * KEEP Enterprise Platform — Extension Framework & Plugin Ecosystem Master Page.
 *
 * Phase: 3.5
 * Specification: devdocs/p3/p3.5.txt & docs/API/api-contract.md (Section 17)
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Blocks,
  Terminal,
  Code2,
  RefreshCw,
  ShoppingBag,
} from 'lucide-react';
import { usePlugins } from '@/hooks/usePlugins';
import {
  PluginMetricsBanner,
  InstalledPluginsList,
  PluginMarketplaceGrid,
  InstallPluginModal,
  PluginConfigModal,
  PluginExecutionLogsDrawer,
  DeveloperSDKDocumentationModal,
} from '@/features/plugins';
import type { PluginItem, PluginMarketplaceItem } from '@/types/plugin';

export const PluginManagementPage: React.FC = () => {
  const {
    installedPlugins,
    marketplaceItems,
    executionLogs,
    analytics,
    selectedPlugin,
    setSelectedPlugin,
    lastExecution,
    loading,
    executing,
    refreshAll,
    installPlugin,
    uninstallPlugin,
    enablePlugin,
    disablePlugin,
    updatePluginConfig,
    executePlugin,
    fetchExecutionLogs,
  } = usePlugins();

  const [activeTab, setActiveTab] = useState<'installed' | 'marketplace'>('installed');
  const [selectedMarketplaceItem, setSelectedMarketplaceItem] = useState<PluginMarketplaceItem | null>(null);
  const [configPlugin, setConfigPlugin] = useState<PluginItem | null>(null);
  const [isLogsDrawerOpen, setIsLogsDrawerOpen] = useState<boolean>(false);
  const [isDocsModalOpen, setIsDocsModalOpen] = useState<boolean>(false);

  const handleOpenExecute = (plugin: PluginItem) => {
    setSelectedPlugin(plugin);
    setIsLogsDrawerOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 lg:p-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-2xl border border-indigo-500/30 text-indigo-400 shadow-lg shadow-indigo-500/10">
            <Blocks className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-white tracking-tight">Plugin SDK & Ecosystem</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Phase 3.5
              </span>
            </div>
            <p className="text-sm text-slate-400">
              Manage extensions, sandboxed LLM connectors, ERP adapters, and bidirectional runtime hooks.
            </p>
          </div>
        </div>

        {/* Global Toolbar Actions */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* SDK Documentation */}
          <button
            onClick={() => setIsDocsModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-200 rounded-xl text-sm font-medium transition-all shadow-sm"
          >
            <Code2 className="w-4 h-4 text-purple-400" /> SDK Docs
          </button>

          {/* Telemetry Logs Drawer */}
          <button
            onClick={() => {
              setSelectedPlugin(null);
              setIsLogsDrawerOpen(true);
            }}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-200 rounded-xl text-sm font-medium transition-all shadow-sm"
          >
            <Terminal className="w-4 h-4 text-cyan-400" /> Execution Telemetry
          </button>

          {/* Refresh All */}
          <button
            onClick={() => void refreshAll()}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Operational Metrics KPI Banner */}
      <PluginMetricsBanner analytics={analytics} />

      {/* View Switcher Tabs */}
      <div className="flex border-b border-slate-800 gap-8">
        <button
          onClick={() => setActiveTab('installed')}
          className={`pb-3 text-sm font-semibold tracking-wide border-b-2 transition-all inline-flex items-center gap-2 ${
            activeTab === 'installed'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Blocks className="w-4 h-4" /> Installed Extensions ({installedPlugins.length})
        </button>

        <button
          onClick={() => setActiveTab('marketplace')}
          className={`pb-3 text-sm font-semibold tracking-wide border-b-2 transition-all inline-flex items-center gap-2 ${
            activeTab === 'marketplace'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShoppingBag className="w-4 h-4" /> Extension Marketplace ({marketplaceItems.length})
        </button>
      </div>

      {/* Main Tab Panels */}
      {activeTab === 'installed' ? (
        <InstalledPluginsList
          plugins={installedPlugins}
          loading={loading}
          onEnable={enablePlugin}
          onDisable={disablePlugin}
          onOpenConfig={(p) => setConfigPlugin(p)}
          onOpenExecute={handleOpenExecute}
          onUninstall={(pluginId) => uninstallPlugin({ plugin_id: pluginId })}
          onRefresh={() => void refreshAll()}
        />
      ) : (
        <PluginMarketplaceGrid
          items={marketplaceItems}
          loading={loading}
          onInstallClick={(item) => setSelectedMarketplaceItem(item)}
          onOpenPublish={() => setIsDocsModalOpen(true)}
        />
      )}

      {/* Interactive Modals and Drawers */}
      <InstallPluginModal
        item={selectedMarketplaceItem}
        onClose={() => setSelectedMarketplaceItem(null)}
        onInstall={installPlugin}
      />

      <PluginConfigModal
        plugin={configPlugin}
        onClose={() => setConfigPlugin(null)}
        onSaveConfig={updatePluginConfig}
      />

      <PluginExecutionLogsDrawer
        isOpen={isLogsDrawerOpen}
        onClose={() => setIsLogsDrawerOpen(false)}
        logs={executionLogs}
        selectedPlugin={selectedPlugin}
        onExecute={executePlugin}
        executing={executing}
        lastExecution={lastExecution}
        onRefreshLogs={() => void fetchExecutionLogs({ limit: 50 })}
      />

      <DeveloperSDKDocumentationModal
        isOpen={isDocsModalOpen}
        onClose={() => setIsDocsModalOpen(false)}
      />
    </div>
  );
};

export default PluginManagementPage;
