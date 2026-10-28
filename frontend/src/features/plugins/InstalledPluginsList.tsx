/**
 * KEEP Enterprise Platform — Installed Extensions & Lifecycle Management.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Settings,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Search,
  Sparkles,
  Link,
  GitBranch,
  Layers,
  BarChart2,
  RefreshCw,
} from 'lucide-react';
import type { PluginItem, PluginCategory } from '@/types/plugin';

interface InstalledPluginsListProps {
  plugins: PluginItem[];
  loading: boolean;
  onEnable: (pluginId: string) => Promise<unknown>;
  onDisable: (pluginId: string) => Promise<unknown>;
  onOpenConfig: (plugin: PluginItem) => void;
  onOpenExecute: (plugin: PluginItem) => void;
  onUninstall: (pluginId: string) => Promise<unknown>;
  onRefresh: () => void;
}

export const InstalledPluginsList: React.FC<InstalledPluginsListProps> = ({
  plugins,
  loading,
  onEnable,
  onDisable,
  onOpenConfig,
  onOpenExecute,
  onUninstall,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [uninstallingId, setUninstallingId] = useState<string | null>(null);

  const filteredPlugins = plugins.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.plugin_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCat = selectedCategory === 'ALL' || p.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const getCategoryBadge = (category: PluginCategory) => {
    switch (category) {
      case 'AI':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Sparkles className="w-3 h-3" /> AI Engine
          </span>
        );
      case 'INTEGRATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Link className="w-3 h-3" /> Integration
          </span>
        );
      case 'WORKFLOW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <GitBranch className="w-3 h-3" /> Workflow
          </span>
        );
      case 'UI':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Layers className="w-3 h-3" /> UI Extension
          </span>
        );
      case 'ANALYTICS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <BarChart2 className="w-3 h-3" /> Analytics
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300">
            {category}
          </span>
        );
    }
  };

  const handleToggle = async (plugin: PluginItem) => {
    try {
      setTogglingId(plugin.plugin_id);
      if (plugin.is_enabled) {
        await onDisable(plugin.plugin_id);
      } else {
        await onEnable(plugin.plugin_id);
      }
    } finally {
      setTogglingId(null);
    }
  };

  const handleUninstall = async (pluginId: string) => {
    if (window.confirm(`Are you sure you want to uninstall plugin '${pluginId}'?`)) {
      try {
        setUninstallingId(pluginId);
        await onUninstall(pluginId);
      } finally {
        setUninstallingId(null);
      }
    }
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white tracking-tight">Installed Extensions</h2>
          <p className="text-sm text-slate-400">
            Manage active runtime hooks, configuration parameters, and execution permissions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Search */}
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search extensions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950/70 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
            />
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-950/70 border border-slate-800 rounded-xl px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-indigo-500/50"
          >
            <option value="ALL">All Categories</option>
            <option value="AI">AI Engines</option>
            <option value="INTEGRATION">Integrations</option>
            <option value="WORKFLOW">Workflows</option>
            <option value="UI">UI Extensions</option>
            <option value="ANALYTICS">Analytics</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-white bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800 transition-colors"
            title="Refresh plugins list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Plugins Table / Grid */}
      {filteredPlugins.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
          <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-slate-300 mb-1">No extensions installed</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Browse the Extension Marketplace to discover and install AI connectors, ERP integrations, and workflow bots.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPlugins.map((plugin) => (
            <div
              key={plugin.id}
              className={`border rounded-xl p-5 transition-all ${
                plugin.is_enabled
                  ? 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  : 'bg-slate-950/40 border-slate-900 opacity-75'
              }`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Left Info */}
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 font-bold text-sm">
                    {plugin.name.charAt(0)}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h4 className="text-base font-semibold text-white tracking-tight">{plugin.name}</h4>
                      {getCategoryBadge(plugin.category)}
                      <span className="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-slate-400 border border-slate-700">
                        v{plugin.version}
                      </span>
                      {plugin.is_enabled ? (
                        <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500 font-medium">
                          <XCircle className="w-3.5 h-3.5" /> Disabled
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-400 line-clamp-2 max-w-2xl mb-2">
                      {plugin.description || 'Enterprise integration package for KEEP Platform.'}
                    </p>

                    {/* Permissions & Hooks tags */}
                    <div className="flex flex-wrap items-center gap-2">
                      {plugin.permissions.map((perm) => (
                        <span
                          key={perm}
                          className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400"
                        >
                          <ShieldCheck className="w-3 h-3 text-indigo-400" />
                          {perm}
                        </span>
                      ))}
                      {plugin.event_hooks.map((hook) => (
                        <span
                          key={hook}
                          className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-cyan-400"
                        >
                          <GitBranch className="w-3 h-3 text-cyan-400" />
                          {hook}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-2 shrink-0 self-end lg:self-center">
                  {/* Status Toggle Switch */}
                  <button
                    onClick={() => handleToggle(plugin)}
                    disabled={togglingId === plugin.plugin_id}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                      plugin.is_enabled ? 'bg-indigo-600' : 'bg-slate-800'
                    }`}
                    title={plugin.is_enabled ? 'Deactivate Extension' : 'Activate Extension'}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        plugin.is_enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>

                  {/* Execute Action */}
                  <button
                    onClick={() => onOpenExecute(plugin)}
                    disabled={!plugin.is_enabled}
                    className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors disabled:opacity-30 disabled:pointer-events-none"
                    title="Invoke Sandbox Action"
                  >
                    <Play className="w-4 h-4" />
                  </button>

                  {/* Settings Config */}
                  <button
                    onClick={() => onOpenConfig(plugin)}
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                    title="Configure Settings"
                  >
                    <Settings className="w-4 h-4" />
                  </button>

                  {/* Uninstall */}
                  <button
                    onClick={() => handleUninstall(plugin.plugin_id)}
                    disabled={uninstallingId === plugin.plugin_id}
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                    title="Uninstall Extension"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
