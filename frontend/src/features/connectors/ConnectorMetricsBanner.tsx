/**
 * Phase 3.1 ConnectorMetricsBanner Component.
 * Displays executive KPI cards for registered enterprise connectors.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  Layers,
  CheckCircle2,
  Database,
  RefreshCw,
  Plus,
  Radio,
} from 'lucide-react';

interface MetricsProps {
  metrics: {
    totalConnectors: number;
    healthyCount: number;
    syncingCount: number;
    errorCount: number;
    totalDocsSynced: number;
  };
  onRegisterClick: () => void;
  onRefreshClick: () => void;
  isLoading: boolean;
}

export const ConnectorMetricsBanner: React.FC<MetricsProps> = ({
  metrics,
  onRegisterClick,
  onRefreshClick,
  isLoading,
}) => {
  return (
    <div className="flex flex-col gap-5">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Enterprise Integrations
            </h1>
            <span className="inline-flex items-center rounded-full bg-indigo-50 dark:bg-indigo-950/70 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
              Phase 3.1
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Connect external SaaS repositories, sync enterprise knowledge, and power unified cross-platform AI search.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onRefreshClick}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/60 transition-colors shadow-sm disabled:opacity-50"
            title="Refresh connectors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-indigo-500' : ''}`} />
            Refresh
          </button>

          <button
            type="button"
            onClick={onRegisterClick}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            <Plus className="w-4 h-4" />
            Connect Platform
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Connectors */}
        <div className="relative overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Total Connectors
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <Layers className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {metrics.totalConnectors}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">configured</span>
          </div>
        </div>

        {/* Card 2: Active & Healthy */}
        <div className="relative overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Active & Healthy
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
              {metrics.healthyCount}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">operational</span>
          </div>
        </div>

        {/* Card 3: Active Synchronization */}
        <div className="relative overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Syncing Now
            </span>
            <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${metrics.syncingCount > 0 ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 animate-pulse' : 'bg-slate-50 dark:bg-slate-800 text-slate-500'}`}>
              <Radio className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {metrics.syncingCount}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {metrics.errorCount > 0 ? `(${metrics.errorCount} attention needed)` : 'active pipelines'}
            </span>
          </div>
        </div>

        {/* Card 4: Documents Synchronized */}
        <div className="relative overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Documents Ingested
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
              <Database className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-blue-600 dark:text-blue-400">
              {metrics.totalDocsSynced.toLocaleString()}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">synced to RAG</span>
          </div>
        </div>
      </div>
    </div>
  );
};
