import React from 'react';
import { GitBranch, ShieldCheck } from 'lucide-react';
import { useAuthorization } from '@/hooks/useAuthorization';
import { useAutonomousWorkflows } from '@/hooks/useAutonomousWorkflows';
import { Permission } from '@/types/permission';
import {
  AutonomousLaunchForm,
  AutonomousWorkflowInspector,
  AutonomousWorkflowList,
} from '@/features/autonomy';

export const AutonomousWorkflowsPage: React.FC = () => {
  const { can } = useAuthorization();
  const canInvoke = can(Permission.AGENT_INVOKE);

  const {
    workflows,
    statusFilter,
    selectedWorkflow,
    steps,
    timeline,
    isLoading,
    isSubmitting,
    isUpdatingAction,
    error,
    setStatusFilter,
    refreshWorkflows,
    startWorkflow,
    inspectWorkflow,
    resumeWorkflow,
    cancelWorkflow,
  } = useAutonomousWorkflows();

  const completedCount = workflows.filter((w) => w.status === 'completed').length;
  const awaitingApprovalCount = workflows.filter((w) => w.status === 'awaiting_approval').length;
  const totalReplans = workflows.reduce((acc, w) => acc + (w.replan_count ?? 0), 0);

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Header & KPI Strip */}
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1.5 flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-800 dark:bg-indigo-950/70 dark:text-indigo-300">
              <GitBranch className="h-3.5 w-3.5" aria-hidden="true" />
              Phase 4.9
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Bounded & Approval-Gated Autonomy
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Autonomous Workflow Engine
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Execute goal-driven workflows with adaptive replanning, strict budget bounds, and
            human-in-the-loop write approvals.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[11px] font-medium text-slate-500">Completed</p>
            <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              {completedCount}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[11px] font-medium text-slate-500">Awaiting Approval</p>
            <p className="text-lg font-bold text-amber-600 dark:text-amber-400">
              {awaitingApprovalCount}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[11px] font-medium text-slate-500">Adaptive Replans</p>
            <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
              {totalReplans}
            </p>
          </div>
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300"
        >
          {error}
        </div>
      )}

      <AutonomousLaunchForm
        isSubmitting={isSubmitting}
        canInvoke={canInvoke}
        onSubmit={startWorkflow}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <AutonomousWorkflowList
            workflows={workflows}
            selectedExecutionId={selectedWorkflow?.execution_id}
            statusFilter={statusFilter}
            isLoading={isLoading}
            onFilterChange={setStatusFilter}
            onSelect={inspectWorkflow}
            onRefresh={refreshWorkflows}
          />
        </div>
        <div className="lg:col-span-7">
          <AutonomousWorkflowInspector
            workflow={selectedWorkflow}
            steps={steps}
            timeline={timeline}
            canInvoke={canInvoke}
            isUpdatingAction={isUpdatingAction}
            onResume={resumeWorkflow}
            onCancel={cancelWorkflow}
          />
        </div>
      </div>
    </div>
  );
};
