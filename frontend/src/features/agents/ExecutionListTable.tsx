/**
 * KEEP Enterprise Platform — Phase 4.2 Execution Ledger Table.
 *
 * Displays tenant-scoped durable agent executions with lifecycle status filter tabs,
 * status badges, attempt tracking, duration metrics, and contextual Inspect / Cancel / Retry actions.
 */

import React from 'react';
import { Eye, RotateCcw, StopCircle } from 'lucide-react';
import type { ExecutionRecordItem, ExecutionStatus } from '@/types/agentRuntime';
import type { StatusFilter } from '@/hooks/useAgentRuntime';

interface ExecutionListTableProps {
  executions: ExecutionRecordItem[];
  statusFilter: StatusFilter;
  loading?: boolean;
  actioningId?: string | null;
  canInvoke?: boolean;
  onFilterChange: (status: StatusFilter) => void;
  onInspect: (record: ExecutionRecordItem) => void;
  onCancel: (executionId: string) => void;
  onRetry: (executionId: string) => void;
}

const FILTER_TABS: Array<{ id: StatusFilter; label: string }> = [
  { id: 'ALL', label: 'All' },
  { id: 'RUNNING', label: 'Running' },
  { id: 'QUEUED', label: 'Queued' },
  { id: 'SUCCEEDED', label: 'Succeeded' },
  { id: 'FAILED', label: 'Failed' },
  { id: 'TIMED_OUT', label: 'Timed Out' },
  { id: 'CANCELLED', label: 'Cancelled' },
];

const STATUS_BADGE_STYLES: Record<ExecutionStatus, string> = {
  PENDING: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200',
  QUEUED: 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300',
  RUNNING: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
  SUCCEEDED: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  FAILED: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
  TIMED_OUT: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  CANCELLED: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200',
};

const NON_TERMINAL: Set<ExecutionStatus> = new Set(['PENDING', 'QUEUED', 'RUNNING']);
const RETRYABLE_STATUS: Set<ExecutionStatus> = new Set(['FAILED', 'TIMED_OUT']);

export const ExecutionListTable: React.FC<ExecutionListTableProps> = ({
  executions,
  statusFilter,
  loading = false,
  actioningId = null,
  canInvoke = true,
  onFilterChange,
  onInspect,
  onCancel,
  onRetry,
}) => {
  return (
    <section className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xs overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Durable Execution Ledger
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Tenant-scoped execution history with atomic lifecycle state transitions & retry lineage.
          </p>
        </div>

        <div
          role="tablist"
          aria-label="Filter executions by status"
          className="flex flex-wrap items-center gap-1.5"
        >
          {FILTER_TABS.map((tab) => {
            const active = statusFilter === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => onFilterChange(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  active
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {loading && executions.length === 0 ? (
        <div className="p-10 text-center text-sm text-gray-500 dark:text-gray-400">
          Loading durable executions...
        </div>
      ) : executions.length === 0 ? (
        <div className="p-10 text-center text-sm text-gray-500 dark:text-gray-400">
          No agent executions match the current filter. Submit a run to begin tracking lifecycle states.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900/50 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400">
              <tr>
                <th scope="col" className="px-6 py-3 text-left font-semibold">
                  Execution / Agent
                </th>
                <th scope="col" className="px-6 py-3 text-left font-semibold">
                  Goal
                </th>
                <th scope="col" className="px-6 py-3 text-left font-semibold">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left font-semibold">
                  Mode / Attempt
                </th>
                <th scope="col" className="px-6 py-3 text-left font-semibold">
                  Duration
                </th>
                <th scope="col" className="px-6 py-3 text-right font-semibold">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {executions.map((exec) => {
                const isNonTerminal = NON_TERMINAL.has(exec.status);
                const isRetryable = RETRYABLE_STATUS.has(exec.status);
                const isBusy = actioningId === exec.execution_id;

                return (
                  <tr
                    key={exec.execution_id}
                    className="hover:bg-gray-50/70 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-gray-900 dark:text-white">
                        {exec.agent_id}{' '}
                        <span className="text-xs font-normal text-gray-500 dark:text-gray-400">
                          v{exec.agent_version}
                        </span>
                      </div>
                      <div className="text-xs font-mono text-gray-500 dark:text-gray-400">
                        {exec.execution_id}
                      </div>
                    </td>

                    <td className="px-6 py-4 max-w-xs">
                      <p className="text-gray-800 dark:text-gray-200 truncate" title={exec.goal}>
                        {exec.goal}
                      </p>
                      {exec.error_code && (
                        <p className="text-xs text-rose-600 dark:text-rose-400 truncate mt-0.5">
                          {exec.error_code}: {exec.error_message}
                        </p>
                      )}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${STATUS_BADGE_STYLES[exec.status]}`}
                      >
                        {exec.status}
                      </span>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600 dark:text-gray-300">
                      <div className="uppercase font-medium">{exec.mode}</div>
                      <div className="text-gray-500 dark:text-gray-400">
                        Attempt #{exec.attempt_number}
                      </div>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600 dark:text-gray-300">
                      {exec.duration_ms !== null ? `${exec.duration_ms} ms` : '—'}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="inline-flex items-center gap-2">
                        {!isNonTerminal && (
                          <button
                            type="button"
                            onClick={() => onInspect(exec)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            Inspect Result
                          </button>
                        )}

                        {isNonTerminal && canInvoke && (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => onCancel(exec.execution_id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-900/30 hover:bg-rose-100 dark:hover:bg-rose-900/50 disabled:opacity-50"
                          >
                            <StopCircle className="w-3.5 h-3.5" />
                            Cancel
                          </button>
                        )}

                        {isRetryable && canInvoke && (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => onRetry(exec.execution_id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 hover:bg-amber-100 dark:hover:bg-amber-900/50 disabled:opacity-50"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
};
