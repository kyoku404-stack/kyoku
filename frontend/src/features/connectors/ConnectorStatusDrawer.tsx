/**
 * Phase 3.1 ConnectorStatusDrawer Component.
 * Slide-out inspection drawer displaying operational health indicators and active telemetry.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  X,
  Activity,
  Zap,
  Gauge,
  CheckCircle2,
  RefreshCw,
  HardDrive,
  Radio,
} from 'lucide-react';
import type { ConnectorStatusResponse } from '@/types/connector';

interface DrawerProps {
  isOpen: boolean;
  status: ConnectorStatusResponse | null;
  onClose: () => void;
  onTriggerSync: (id: string) => void;
  isSyncing: boolean;
}

export const ConnectorStatusDrawer: React.FC<DrawerProps> = ({
  isOpen,
  status,
  onClose,
  onTriggerSync,
  isSyncing,
}) => {
  if (!isOpen || !status) return null;

  const { health_metrics: health } = status;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-md border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl flex flex-col justify-between">
          <div>
            {/* Drawer Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white line-clamp-1" title={status.name}>
                    {status.name}
                  </h2>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {status.platform_type.replace('_', ' ')} Telemetry
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Overall Status Badge */}
            <div className="mt-5 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Operational Status
              </span>
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="w-3.5 h-3.5" /> {status.status}
              </span>
            </div>

            {/* Health Telemetry Metrics */}
            <div className="mt-5 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Health & SLA Telemetry
              </h3>

              {/* Latency */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span>API Response Latency</span>
                  </div>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {health.api_latency_ms.toFixed(1)} ms
                  </span>
                </div>
                <div className="mt-2 text-xs text-emerald-600 dark:text-emerald-400">
                  Well within 5000ms SLA target
                </div>
              </div>

              {/* Quota Usage */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                    <Gauge className="w-4 h-4 text-indigo-500" />
                    <span>API Quota Consumption</span>
                  </div>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {health.quota_used_pct.toFixed(1)}%
                  </span>
                </div>
                {/* Progress bar */}
                <div className="mt-2.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, Math.max(5, health.quota_used_pct))}%` }}
                  />
                </div>
              </div>

              {/* Success Rate */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span>Sync Success Rate</span>
                  </div>
                  <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                    {health.success_rate_pct.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Ingestion footprint */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                  <HardDrive className="w-4 h-4 text-blue-500" />
                  <span>Total Ingested Documents</span>
                </div>
                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                  {status.total_documents_synced.toLocaleString()} docs
                </span>
              </div>
            </div>

            {/* Active Sync Info */}
            {status.active_sync_job && (
              <div className="mt-5 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-200">
                <div className="flex items-center gap-2 font-semibold">
                  <Radio className="w-4 h-4 animate-spin text-amber-600" />
                  <span>Active Synchronization Job Running</span>
                </div>
                <p className="mt-1">
                  Mode: {status.active_sync_job.sync_mode} | Discovered: {status.active_sync_job.documents_discovered} resources
                </p>
              </div>
            )}
          </div>

          {/* Footer Action */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              Close
            </button>
            <button
              type="button"
              onClick={() => onTriggerSync(status.id)}
              disabled={isSyncing}
              className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing ? 'Syncing...' : 'Trigger Sync'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
