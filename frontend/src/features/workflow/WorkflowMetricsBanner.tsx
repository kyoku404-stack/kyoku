/**
 * Phase 3.4 WorkflowMetricsBanner Component.
 * Displays high-level workflow automation metrics and quick action controls.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  Zap,
  Play,
  CheckCircle2,
  Clock,
  Bell,
  Sliders,
  Plus,
  RefreshCw,
} from 'lucide-react';
import type { WorkflowAnalyticsData } from '@/types/workflow';

interface WorkflowMetricsBannerProps {
  analytics: WorkflowAnalyticsData | null;
  pendingApprovalsCount: number;
  unreadNotificationsCount: number;
  onOpenCreateModal: () => void;
  onOpenPreferencesModal: () => void;
  onOpenNotificationsDrawer: () => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const WorkflowMetricsBanner: React.FC<WorkflowMetricsBannerProps> = ({
  analytics,
  pendingApprovalsCount,
  unreadNotificationsCount,
  onOpenCreateModal,
  onOpenPreferencesModal,
  onOpenNotificationsDrawer,
  onRefresh,
  isLoading,
}) => {
  const successRate = analytics?.success_rate ?? 100;
  const totalWorkflows = analytics?.total_workflows ?? 0;
  const activeWorkflows = analytics?.active_workflows ?? 0;
  const totalExecutions = analytics?.total_executions ?? 0;
  const avgDuration = analytics?.average_duration_ms ? `${(analytics.average_duration_ms / 1000).toFixed(2)}s` : '0.0s';

  return (
    <div className="flex flex-col gap-5">
      {/* Top Header & Action Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Workflow Automation & Intelligence
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Event-Driven Workflows, Human-in-the-Loop Approvals & Multi-Channel Notifications
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={onOpenNotificationsDrawer}
            className="relative inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors shadow-sm"
          >
            <Bell className="w-4 h-4 text-indigo-500" />
            <span>Inbox</span>
            {unreadNotificationsCount > 0 && (
              <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white bg-rose-500 rounded-full">
                {unreadNotificationsCount}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={onOpenPreferencesModal}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors shadow-sm"
          >
            <Sliders className="w-4 h-4 text-slate-500" />
            <span>Preferences</span>
          </button>

          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <button
            type="button"
            onClick={onOpenCreateModal}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-600/25"
          >
            <Plus className="w-4 h-4" />
            <span>New Workflow</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Workflows */}
        <div className="p-4 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Active Workflows
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {activeWorkflows}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                / {totalWorkflows} total
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
            <Zap className="w-5 h-5" />
          </div>
        </div>

        {/* Total Executions */}
        <div className="p-4 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Total Executions
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {totalExecutions}
              </span>
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                avg {avgDuration}
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <Play className="w-5 h-5" />
          </div>
        </div>

        {/* Success Rate */}
        <div className="p-4 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Success Rate
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {successRate.toFixed(1)}%
              </span>
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                SLA 99.9%
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="p-4 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Pending Approvals
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {pendingApprovalsCount}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                human-in-the-loop
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <Clock className="w-5 h-5" />
          </div>
        </div>
      </div>
    </div>
  );
};
