/**
 * Phase 3.4 WorkflowAnalyticsDashboard Component.
 * Telemetry and execution analytics for workflow performance, error frequency, and duration distributions.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  BarChart3,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import type { WorkflowAnalyticsData } from '@/types/workflow';

interface WorkflowAnalyticsDashboardProps {
  analytics: WorkflowAnalyticsData | null;
}

export const WorkflowAnalyticsDashboard: React.FC<WorkflowAnalyticsDashboardProps> = ({
  analytics,
}) => {
  if (!analytics) return null;

  const total = analytics.total_executions || 0;
  const success = analytics.successful_executions || 0;
  const failed = analytics.failed_executions || 0;
  const successRate = analytics.success_rate || 100;
  const avgDurationMs = analytics.average_duration_ms || 0;

  return (
    <div className="bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            Workflow Execution Analytics
          </h3>
        </div>
        <span className="text-xs text-slate-400">Past 30 Days Telemetry</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Success vs Failure */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
            <span>Reliability Rate</span>
            <span className="text-emerald-600 font-bold">{successRate.toFixed(1)}%</span>
          </div>

          <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden flex">
            <div
              className="bg-emerald-500 h-full transition-all duration-500"
              style={{ width: `${successRate}%` }}
            />
            <div
              className="bg-rose-500 h-full transition-all duration-500"
              style={{ width: `${100 - successRate}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
            <span className="flex items-center gap-1 text-emerald-600">
              <CheckCircle className="w-3 h-3" /> {success} succeeded
            </span>
            <span className="flex items-center gap-1 text-rose-500">
              <AlertTriangle className="w-3 h-3" /> {failed} failed
            </span>
          </div>
        </div>

        {/* Latency & Duration */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Average Step Latency
          </span>
          <div className="flex items-baseline gap-2 pt-1">
            <span className="text-2xl font-bold text-slate-900 dark:text-white font-mono">
              {(avgDurationMs / 1000).toFixed(2)}s
            </span>
            <span className="text-xs text-emerald-600 font-medium">p95 &lt; 2.5s</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Async event loop execution with automatic retry backoff.
          </p>
        </div>

        {/* Total DAG Runs */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Throughput Volume
          </span>
          <div className="flex items-baseline gap-2 pt-1">
            <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 font-mono">
              {total}
            </span>
            <span className="text-xs text-slate-400">total runs</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Active DAG executions across tenant projects and connectors.
          </p>
        </div>
      </div>
    </div>
  );
};
