import React from 'react';
import type { FeedbackType, IntelligenceInsight } from '@/types/proactiveIntelligence';

interface Props {
  insight: IntelligenceInsight | null;
  actionLoading: boolean;
  feedbackNotice: string | null;
  onFeedback: (insightId: string, feedback: FeedbackType) => void;
  onDismiss: (insightId: string) => void;
  onResolve: (insightId: string) => void;
  onInvestigate: (insightId: string) => void;
}

const FEEDBACK_OPTIONS: Array<{ value: FeedbackType; label: string }> = [
  { value: 'useful', label: 'Useful' },
  { value: 'already_known', label: 'Already Known' },
  { value: 'irrelevant', label: 'Irrelevant' },
  { value: 'needs_more_evidence', label: 'Needs More Evidence' },
];

export const IntelligenceDetailPanel: React.FC<Props> = ({
  insight,
  actionLoading,
  feedbackNotice,
  onFeedback,
  onDismiss,
  onResolve,
  onInvestigate,
}) => {
  if (!insight) {
    return (
      <section
        aria-label="Insight details"
        className="flex min-h-[320px] items-center justify-center rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-800"
      >
        Select an insight from the feed to inspect evidence, provenance, and actions.
      </section>
    );
  }

  return (
    <section
      aria-label="Insight details"
      className="space-y-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-3 dark:border-slate-700">
        <div>
          <span className="text-xs font-medium uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
            {insight.category.replace('_', ' ')} • {insight.status}
          </span>
          <h2 className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
            {insight.title}
          </h2>
        </div>
        <div className="text-right text-xs text-slate-600 dark:text-slate-400">
          <div>Priority: {insight.priority_score.toFixed(1)} / 100</div>
          <div>Confidence: {Math.round(insight.confidence_score * 100)}%</div>
        </div>
      </div>

      <p className="text-sm text-slate-700 dark:text-slate-300">{insight.summary}</p>

      {insight.observed_facts.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Observed Facts
          </h3>
          <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
            {insight.observed_facts.map((fact, idx) => (
              <li key={idx}>{fact}</li>
            ))}
          </ul>
        </div>
      )}

      {insight.inferred_explanation && (
        <div className="rounded bg-slate-50 p-3 text-sm text-slate-700 dark:bg-slate-900/60 dark:text-slate-300">
          <span className="font-semibold">Explanation: </span>
          {insight.inferred_explanation}
        </div>
      )}

      {insight.limitations.length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          <p className="font-semibold">Limitations & Caveats</p>
          <ul className="mt-1 list-disc pl-4">
            {insight.limitations.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Authorized Evidence ({insight.evidence_records?.length || insight.evidence_refs.length})
        </h3>
        <ul className="mt-1.5 space-y-1.5">
          {(insight.evidence_records?.length
            ? insight.evidence_records
            : insight.evidence_refs.map((ref) => ({
                evidence_id: ref,
                resource_ref: ref,
                source_type: 'document',
                validation_outcome: 'valid' as const,
                snippet: null,
              }))
          ).map((ev) => (
            <li
              key={ev.evidence_id}
              className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-900/40"
            >
              <div className="flex items-center justify-between font-medium">
                <span>{ev.resource_ref}</span>
                <span className="text-emerald-700 dark:text-emerald-400">
                  {ev.validation_outcome}
                </span>
              </div>
              {ev.snippet && <p className="mt-1 text-slate-600 dark:text-slate-400">{ev.snippet}</p>}
            </li>
          ))}
        </ul>
      </div>

      {insight.workflow_execution_id && (
        <div className="rounded border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs text-indigo-900 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-200">
          Investigation Workflow Linked: <code>{insight.workflow_execution_id}</code>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 border-t border-slate-200 pt-3 dark:border-slate-700">
        <button
          type="button"
          disabled={actionLoading || insight.status === 'resolved'}
          onClick={() => onInvestigate(insight.insight_id)}
          className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Investigate Workflow
        </button>
        <button
          type="button"
          disabled={actionLoading || insight.status === 'resolved'}
          onClick={() => onResolve(insight.insight_id)}
          className="rounded bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Mark Resolved
        </button>
        <button
          type="button"
          disabled={actionLoading}
          onClick={() => onDismiss(insight.insight_id)}
          className="rounded border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:text-slate-200"
        >
          Dismiss
        </button>
      </div>

      <div className="border-t border-slate-200 pt-3 dark:border-slate-700">
        <p className="text-xs font-medium text-slate-500">Was this insight helpful?</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {FEEDBACK_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              disabled={actionLoading}
              onClick={() => onFeedback(insight.insight_id, opt.value)}
              className="rounded border border-slate-300 px-2.5 py-1 text-xs hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
            >
              {opt.label}
            </button>
          ))}
        </div>
        {feedbackNotice && (
          <p role="status" className="mt-2 text-xs text-emerald-700 dark:text-emerald-400">
            {feedbackNotice}
          </p>
        )}
      </div>
    </section>
  );
};
