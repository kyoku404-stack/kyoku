import React from 'react';
import { FileSearch, FileText, RefreshCw, XCircle } from 'lucide-react';
import type { ResearchRunRecord, ResearchStatus } from '@/types/research';

interface ResearchRunListProps {
  runs: ResearchRunRecord[];
  statusFilter: ResearchStatus | 'all';
  selectedRunId: string | null;
  isLoading: boolean;
  canInvoke: boolean;
  onFilterChange: (status: ResearchStatus | 'all') => void;
  onRefresh: () => void;
  onInspectReport: (researchId: string) => void;
  onInspectEvidence: (researchId: string) => void;
  onCancelRun: (researchId: string) => void;
}

const STATUS_TABS: Array<{ id: ResearchStatus | 'all'; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'completed', label: 'Completed' },
  { id: 'insufficient_evidence', label: 'Insufficient Evidence' },
  { id: 'partial', label: 'Partial' },
  { id: 'running', label: 'Running' },
  { id: 'failed', label: 'Failed' },
];

const STATUS_BADGE_CLASSES: Record<ResearchStatus, string> = {
  pending: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  running: 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300',
  completed: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300',
  partial: 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300',
  insufficient_evidence: 'bg-orange-100 text-orange-800 dark:bg-orange-950/60 dark:text-orange-300',
  failed: 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300',
  cancelled: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400',
};

export const ResearchRunList: React.FC<ResearchRunListProps> = ({
  runs,
  statusFilter,
  selectedRunId,
  isLoading,
  canInvoke,
  onFilterChange,
  onRefresh,
  onInspectReport,
  onInspectEvidence,
  onCancelRun,
}) => {
  return (
    <section
      aria-label="Research Investigations Ledger"
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div
          role="tablist"
          aria-label="Filter research runs by status"
          className="flex flex-wrap items-center gap-1.5"
        >
          {STATUS_TABS.map((tab) => {
            const active = statusFilter === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                type="button"
                aria-selected={active}
                onClick={() => onFilterChange(tab.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                  active
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
          Refresh
        </button>
      </div>

      {runs.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          {isLoading
            ? 'Loading tenant research investigations...'
            : 'No research investigations match this filter yet.'}
        </div>
      ) : (
        <div className="space-y-3">
          {runs.map((run) => {
            const isSelected = selectedRunId === run.research_id;
            const isReportReady =
              run.status === 'completed' ||
              run.status === 'partial' ||
              run.status === 'insufficient_evidence';
            const isActive = run.status === 'pending' || run.status === 'running';

            return (
              <article
                key={run.research_id}
                className={`rounded-lg border p-4 transition-colors ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50/40 dark:border-indigo-400 dark:bg-indigo-950/20'
                    : 'border-slate-200 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/40'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${STATUS_BADGE_CLASSES[run.status]}`}
                      >
                        {run.status.replace('_', ' ')}
                      </span>
                      <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                        {run.research_id}
                      </span>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400">
                        {run.sources_retained}/{run.sources_retrieved} sources retained
                      </span>
                      {run.contradictions.length > 0 && (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-800 dark:bg-amber-950/70 dark:text-amber-300">
                          {run.contradictions.length} contradiction
                          {run.contradictions.length > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {run.question}
                    </h3>
                    {run.scope && (
                      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                        Scope: {run.scope}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {isReportReady && (
                      <button
                        type="button"
                        onClick={() => onInspectReport(run.research_id)}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
                      >
                        <FileText className="h-3.5 w-3.5" aria-hidden="true" />
                        Inspect Report
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onInspectEvidence(run.research_id)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                    >
                      <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
                      Evidence
                    </button>
                    {isActive && canInvoke && (
                      <button
                        type="button"
                        onClick={() => onCancelRun(run.research_id)}
                        className="inline-flex items-center gap-1 rounded-lg border border-rose-300 bg-rose-50 px-2.5 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                      >
                        <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
};
