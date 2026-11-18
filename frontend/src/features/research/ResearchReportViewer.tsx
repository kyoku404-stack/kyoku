import React from 'react';
import { AlertTriangle, BookOpenCheck, CheckCircle2, HelpCircle, Lightbulb, ShieldAlert } from 'lucide-react';
import type { ConfidenceLevel, ResearchReport } from '@/types/research';

interface ResearchReportViewerProps {
  report: ResearchReport | null;
  isLoading: boolean;
  onCitationClick: (researchId: string, evidenceId: string) => void;
  onOpenAllEvidence: (researchId: string) => void;
}

const CONFIDENCE_STYLES: Record<ConfidenceLevel, string> = {
  high: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300',
  medium: 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300',
  low: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
};

export const ResearchReportViewer: React.FC<ResearchReportViewerProps> = ({
  report,
  isLoading,
  onCitationClick,
  onOpenAllEvidence,
}) => {
  if (isLoading) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        Loading evidence-backed research report...
      </section>
    );
  }

  if (!report) {
    return (
      <section className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
        Launch a new investigation or select <strong>Inspect Report</strong> from the ledger to view
        citation-verified findings, contradictions, and source provenance.
      </section>
    );
  }

  return (
    <section
      aria-label="Research Report Viewer"
      className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      {/* Header & Metrics */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-2.5 py-0.5 font-semibold text-indigo-800 dark:bg-indigo-950/70 dark:text-indigo-300">
              <BookOpenCheck className="h-3.5 w-3.5" aria-hidden="true" />
              {report.status.replace('_', ' ')}
            </span>
            <span className="font-mono text-slate-500 dark:text-slate-400">{report.research_id}</span>
            <span className="text-slate-500 dark:text-slate-400">
              Sources: {report.sources_retained} retained / {report.sources_retrieved} retrieved
            </span>
            {report.correction_attempts > 0 && (
              <span className="rounded-full bg-sky-100 px-2 py-0.5 font-medium text-sky-800 dark:bg-sky-950/60 dark:text-sky-300">
                Self-corrected ({report.correction_attempts})
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">{report.question}</h2>
          <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{report.summary}</p>
        </div>

        <button
          type="button"
          onClick={() => onOpenAllEvidence(report.research_id)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3.5 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
        >
          View Provenance ({report.evidence.length})
        </button>
      </div>

      {/* Insufficient Evidence Banner */}
      {report.status === 'insufficient_evidence' && (
        <div
          role="status"
          className="flex items-start gap-3 rounded-lg border border-orange-300 bg-orange-50 p-4 text-sm text-orange-900 dark:border-orange-800 dark:bg-orange-950/40 dark:text-orange-200"
        >
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
          <div>
            <p className="font-semibold">Insufficient Authorized Evidence</p>
            <p className="mt-0.5 text-xs">
              KEEP found no authorized internal passages answering this question and returned zero
              speculative findings.
            </p>
          </div>
        </div>
      )}

      {/* Warnings */}
      {report.warnings.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
          <p className="mb-1 font-semibold">Quality & Governance Notices</p>
          <ul className="list-disc space-y-0.5 pl-4">
            {report.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Contradictions Callout */}
      {report.contradictions.length > 0 && (
        <div
          aria-label="Cross-Source Contradictions"
          className="rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/40"
        >
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-900 dark:text-amber-200">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
            Surfaced Contradictions ({report.contradictions.length})
          </div>
          <div className="space-y-2.5">
            {report.contradictions.map((item, idx) => (
              <div key={idx} className="text-xs text-amber-900 dark:text-amber-100">
                <p className="font-semibold">{item.topic}</p>
                <p className="mt-0.5">{item.description}</p>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  {item.evidence_ids.map((eid) => (
                    <button
                      key={eid}
                      type="button"
                      onClick={() => onCitationClick(report.research_id, eid)}
                      className="rounded bg-amber-200/80 px-2 py-0.5 font-mono text-[11px] font-semibold text-amber-950 hover:bg-amber-300 dark:bg-amber-900 dark:text-amber-100"
                    >
                      [{eid}]
                    </button>
                  ))}
                  {item.source_dates.length > 0 && (
                    <span className="text-[11px] text-amber-800 dark:text-amber-300">
                      Dates: {item.source_dates.join(' vs ')}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Grounded Findings */}
      {report.findings.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
            Synthesized Findings ({report.findings.length})
          </h3>
          <div className="space-y-3">
            {report.findings.map((finding) => (
              <article
                key={finding.finding_id}
                className="rounded-lg border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-950/50"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px]">
                  <span className="font-mono font-semibold text-slate-500">
                    {finding.finding_id}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 font-semibold uppercase ${CONFIDENCE_STYLES[finding.confidence]}`}
                  >
                    {finding.confidence} confidence
                  </span>
                  <span className="rounded-full bg-slate-200 px-2 py-0.5 font-medium capitalize text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                    {finding.claim_type}
                  </span>
                  {finding.has_contradiction && (
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 font-semibold text-amber-800 dark:bg-amber-950/70 dark:text-amber-300">
                      Contradiction Flagged
                    </span>
                  )}
                </div>

                <p className="text-sm text-slate-900 dark:text-slate-100">{finding.claim}</p>

                {finding.evidence_ids.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] font-medium text-slate-500">Citations:</span>
                    {finding.evidence_ids.map((eid) => (
                      <button
                        key={eid}
                        type="button"
                        onClick={() => onCitationClick(report.research_id, eid)}
                        className="rounded-md border border-indigo-200 bg-indigo-50 px-2 py-0.5 font-mono text-[11px] font-semibold text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
                      >
                        [{eid}]
                      </button>
                    ))}
                  </div>
                )}

                {finding.limitations.length > 0 && (
                  <ul className="mt-2 list-disc space-y-0.5 pl-4 text-xs text-slate-500 dark:text-slate-400">
                    {finding.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                )}
              </article>
            ))}
          </div>
        </div>
      )}

      {/* Unresolved Questions & Follow-Up Suggestions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
          <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">
            <HelpCircle className="h-3.5 w-3.5 text-amber-600" aria-hidden="true" />
            Unresolved Questions ({report.unresolved_questions.length})
          </h3>
          {report.unresolved_questions.length === 0 ? (
            <p className="text-xs text-slate-500">No unresolved coverage gaps flagged.</p>
          ) : (
            <ul className="list-disc space-y-1 pl-4 text-xs text-slate-700 dark:text-slate-300">
              {report.unresolved_questions.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
          <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-300">
            <Lightbulb className="h-3.5 w-3.5 text-indigo-600" aria-hidden="true" />
            Follow-Up Suggestions ({report.follow_up_suggestions.length})
          </h3>
          {report.follow_up_suggestions.length === 0 ? (
            <p className="text-xs text-slate-500">No additional follow-ups suggested.</p>
          ) : (
            <ul className="list-disc space-y-1 pl-4 text-xs text-slate-700 dark:text-slate-300">
              {report.follow_up_suggestions.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
};
