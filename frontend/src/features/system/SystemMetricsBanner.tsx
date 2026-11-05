/**
 * KEEP Enterprise Platform — Production Infrastructure & Metrics KPI Banner.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  Layers,
  Zap,
} from 'lucide-react';
import type { SystemHealthData, SystemMetricsData } from '@/types/system';

interface SystemMetricsBannerProps {
  health: SystemHealthData | null;
  metrics: SystemMetricsData | null;
  onViewSubsystems?: () => void;
}

export const SystemMetricsBanner: React.FC<SystemMetricsBannerProps> = ({
  health,
  metrics,
  onViewSubsystems,
}) => {
  const healthStatus = health?.status ?? 'UNKNOWN';
  const overallScorePct = Math.round((health?.overall_score ?? 1.0) * 100);
  const cpuPercent = metrics?.cpu.percent ?? 0;
  const memPercent = metrics?.memory.percent ?? 0;
  const diskPercent = metrics?.disk.percent ?? 0;
  const rps = metrics?.application.requests_per_second ?? 0;
  const p95Latency = metrics?.application.p95_latency_ms ?? 0;
  const cacheHitPct = metrics?.cache.hit_ratio_percent ?? 0;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-400 shadow-emerald-500/50',
          text: 'text-emerald-400',
        };
      case 'DEGRADED':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          dot: 'bg-amber-400 shadow-amber-500/50',
          text: 'text-amber-400',
        };
      default:
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          dot: 'bg-rose-400 shadow-rose-500/50',
          text: 'text-rose-400',
        };
    }
  };

  const statusTheme = getStatusColor(healthStatus);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
      {/* 1. Health & Status Score */}
      <div
        className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/50 transition-all cursor-pointer"
        onClick={onViewSubsystems}
        title="Click to view subsystem diagnostic breakdown"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Platform Health</span>
          <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400 group-hover:scale-110 transition-transform">
            <Activity className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full animate-pulse ${statusTheme.dot}`} />
          <span className={`text-xl font-bold tracking-tight ${statusTheme.text}`}>
            {healthStatus}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
          <span>Score: {overallScorePct}%</span>
          <span className="text-indigo-400 hover:underline">Subsystems &rarr;</span>
        </div>
      </div>

      {/* 2. CPU Utilization */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-cyan-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">CPU Load</span>
          <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-400 group-hover:scale-110 transition-transform">
            <Cpu className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{cpuPercent}%</span>
          <span className="text-xs text-slate-400">{metrics?.cpu.cores ?? 8} cores</span>
        </div>
        <div className="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full ${cpuPercent > 80 ? 'bg-rose-500' : 'bg-cyan-400'}`}
            style={{ width: `${Math.min(100, Math.max(0, cpuPercent))}%` }}
          />
        </div>
      </div>

      {/* 3. Memory Utilization */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-purple-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Memory</span>
          <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400 group-hover:scale-110 transition-transform">
            <Layers className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{memPercent}%</span>
          <span className="text-xs text-slate-400">
            {metrics ? `${Math.round(metrics.memory.used_mb / 1024)}GB` : 'RAM'}
          </span>
        </div>
        <div className="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full ${memPercent > 85 ? 'bg-rose-500' : 'bg-purple-400'}`}
            style={{ width: `${Math.min(100, Math.max(0, memPercent))}%` }}
          />
        </div>
      </div>

      {/* 4. Storage Headroom */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-blue-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Disk Storage</span>
          <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400 group-hover:scale-110 transition-transform">
            <HardDrive className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{diskPercent}%</span>
          <span className="text-xs text-slate-400">
            {metrics ? `${Math.round(metrics.disk.used_gb)}GB used` : 'Volume'}
          </span>
        </div>
        <div className="mt-2 text-xs text-slate-400">
          Headroom: {Math.max(0, Math.round(100 - diskPercent))}% free
        </div>
      </div>

      {/* 5. Application Traffic & Latency */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-amber-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Throughput</span>
          <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400 group-hover:scale-110 transition-transform">
            <Zap className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{rps}</span>
          <span className="text-xs text-slate-400">req/s</span>
        </div>
        <div className="mt-2 text-xs text-slate-400">
          p95 Latency: <span className="text-amber-400 font-semibold">{p95Latency}ms</span>
        </div>
      </div>

      {/* 6. Redis Multi-Tier Cache */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md relative overflow-hidden group hover:border-rose-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Cache Layer</span>
          <div className="p-2 bg-rose-500/10 rounded-lg text-rose-400 group-hover:scale-110 transition-transform">
            <Database className="w-5 h-5" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white tracking-tight">{cacheHitPct}%</span>
          <span className="text-xs text-slate-400">hit ratio</span>
        </div>
        <div className="mt-2 text-xs text-slate-400">
          Keys: {metrics?.cache.total_keys.toLocaleString() ?? '0'} cached
        </div>
      </div>
    </div>
  );
};
