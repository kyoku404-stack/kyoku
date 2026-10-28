/**
 * KEEP Enterprise Platform — Plugin Metrics & KPI Banner.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import { Blocks, Activity, Zap, Clock, AlertTriangle } from 'lucide-react';
import type { PluginAnalytics } from '@/types/plugin';

interface PluginMetricsBannerProps {
  analytics: PluginAnalytics | null;
}

export const PluginMetricsBanner: React.FC<PluginMetricsBannerProps> = ({ analytics }) => {
  const totalInstalled = analytics?.total_installed_plugins ?? 0;
  const activePlugins = analytics?.active_plugins ?? 0;
  const totalExecutions = analytics?.total_executions ?? 0;
  const avgLatency = analytics?.avg_latency_ms ?? 0;
  const errorRate = analytics?.error_rate ?? 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {/* Total Installed */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-indigo-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Installed Plugins</span>
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 group-hover:scale-110 transition-transform">
            <Blocks className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{totalInstalled}</span>
          <span className="text-xs text-slate-400 font-normal">extensions</span>
        </div>
        <div className="mt-2 text-xs text-indigo-400 font-medium">Tenant workspace active</div>
        <div className="absolute -bottom-6 -right-6 w-16 h-16 bg-indigo-500/5 rounded-full blur-xl pointer-events-none" />
      </div>

      {/* Active Plugins */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Active Extensions</span>
          <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400 group-hover:scale-110 transition-transform">
            <Activity className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{activePlugins}</span>
          <span className="text-xs text-slate-400 font-normal">of {totalInstalled} enabled</span>
        </div>
        <div className="mt-2 text-xs text-emerald-400 font-medium">Listening to hooks</div>
        <div className="absolute -bottom-6 -right-6 w-16 h-16 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
      </div>

      {/* Total Executions */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-blue-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Total Invocations</span>
          <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 group-hover:scale-110 transition-transform">
            <Zap className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{totalExecutions.toLocaleString()}</span>
          <span className="text-xs text-slate-400 font-normal">dispatched</span>
        </div>
        <div className="mt-2 text-xs text-blue-400 font-medium">Direct API & Hook events</div>
        <div className="absolute -bottom-6 -right-6 w-16 h-16 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
      </div>

      {/* Average Latency */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-amber-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Avg Sandbox Latency</span>
          <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400 group-hover:scale-110 transition-transform">
            <Clock className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{avgLatency}</span>
          <span className="text-xs text-slate-400 font-normal">ms</span>
        </div>
        <div className="mt-2 text-xs text-amber-400 font-medium">Sandboxed isolation SLA</div>
        <div className="absolute -bottom-6 -right-6 w-16 h-16 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
      </div>

      {/* Error Rate */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-rose-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Error Rate</span>
          <div className="p-2 bg-rose-500/10 rounded-lg text-rose-400 group-hover:scale-110 transition-transform">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{errorRate}%</span>
          <span className="text-xs text-slate-400 font-normal">failures</span>
        </div>
        <div className="mt-2 text-xs text-rose-400 font-medium">Fault-trapped executions</div>
        <div className="absolute -bottom-6 -right-6 w-16 h-16 bg-rose-500/5 rounded-full blur-xl pointer-events-none" />
      </div>
    </div>
  );
};
