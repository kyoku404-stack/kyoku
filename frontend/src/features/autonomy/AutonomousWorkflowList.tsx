import React from 'react';
import { RefreshCw } from 'lucide-react';
import type { AutonomousWorkflowRecord, AutonomyStatus } from '@/types/autonomy';

interface AutonomousWorkflowListProps {
  workflows: AutonomousWorkflowRecord[];
  selectedExecutionId?: string;
  statusFilter: AutonomyStatus | 'all';
  isLoading: boolean;
  onFilterChange: (status: AutonomyStatus | 'all') => void;
  onSelect: (executionId: string) => void;
  onRefresh: () => void;
}

const FILTER_TABS: Array<{ value: AutonomyStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'completed', label: 'Completed' },
  { value: 'awaiting_approval', label: 'Awaiting Approval' },
  { value: 'running', label: 'Running' },
  { value: 'budget_exhausted', label: 'Budget Exhausted' },
  { value: 'cancelled', label: 'Cancelled' },
];

const STATUS_BADGE_MAP: Record<AutonomyStatus, string> = {
  pending: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  running: 'bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300',
  awaiting_approval: 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300',
  completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300',
  failed: 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300',
  budget_exhausted: 'bg-orange-100 text-orange-800 dark:bg-orange-950/60 dark:text-orange-300',
  cancelled: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400',
};

export const AutonomousWorkflowList: React.FC<AutonomousWorkflowListProps> = ({
  workflows,
  selectedExecutionId,
  statusFilter,
  isLoading,
  onFilterChange,
  onSelect,
  onRefresh,
}) => {
  return (
    <section
      aria-labelledby="autonomy-list-heading"
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2
          id="autonomy-list-heading"
          className="text-sm font-semibold text-slate-900 dark:text-slate-100"
        >
          Autonomous Executions
        </h2>
        <button
          type="button"
          onClick={onRefresh}
          aria-label="Refresh autonomous workflows"
          className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
          Refresh
        </button>
      </div>

      {/* Accessible status filter tabs */}
      <div role="tablist" aria-label="Filter autonomous workflows by status" className="mb-3 flex flex-wrap gap-1">
        {FILTER_TABS.map((tab) => {
          const active = statusFilter === tab.value;
          return (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onFilterChange(tab.value)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                active
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {workflows.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500 dark:border-slate-800">
          No autonomous workflows found for this filter. Launch a goal above to begin.
        </p>
      ) : (
        <ul className="space-y-2" aria-label="Autonomous workflow execution list">
          {workflows.map((wf) => {
            const isSelected = wf.execution_id === selectedExecutionId;
            return (
              <li key={wf.execution_id}>
                <button
                  type="button"
                  onClick={() => onSelect(wf.execution_id)}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-50/50 dark:border-indigo-500 dark:bg-indigo-950/30'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950'
                  }`}
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-mono text-[11px] text-slate-500">{wf.execution_id}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                        STATUS_BADGE_MAP[wf.status]
                      }`}
                    >
                      {wf.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="line-clamp-2 text-xs font-medium text-slate-900 dark:text-slate-100">
                    {wf.objective}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                    <span>Type: {wf.workflow_id}</span>
                    <span>•</span>
                    <span>
                      Steps: {wf.budget?.steps_consumed ?? wf.current_step_index}/{wf.policy.max_steps}
                    </span>
                    <span>•</span>
                    <span>Replans: {wf.replan_count}/{wf.policy.max_replans}</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
};
