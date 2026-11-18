import React, { useEffect } from 'react';
import { Calendar, FileCheck2, Lock, X } from 'lucide-react';
import type { EvidenceItem } from '@/types/research';

interface EvidenceProvenanceDrawerProps {
  isOpen: boolean;
  isLoading: boolean;
  evidenceItems: EvidenceItem[];
  redactedCount: number;
  highlightedEvidenceId: string | null;
  onClose: () => void;
}

export const EvidenceProvenanceDrawer: React.FC<EvidenceProvenanceDrawerProps> = ({
  isOpen,
  isLoading,
  evidenceItems,
  redactedCount,
  highlightedEvidenceId,
  onClose,
}) => {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/50 backdrop-blur-xs">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Evidence Provenance Drawer"
        className="flex h-full w-full max-w-xl flex-col border-l border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Evidence Provenance & Citations
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Re-authorized internal KEEP source passages bound to this investigation.
            </p>
          </div>
          <button
            type="button"
            aria-label="Close Drawer"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {redactedCount > 0 && (
            <div className="mb-4 flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
              <Lock className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>
                {redactedCount} restricted source passage(s) were omitted based on your current
                access permissions.
              </span>
            </div>
          )}

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading authorized evidence passages...</p>
          ) : evidenceItems.length === 0 ? (
            <p className="text-sm text-slate-500">
              No authorized evidence passages are recorded for this investigation.
            </p>
          ) : (
            <div className="space-y-3">
              {evidenceItems.map((item) => {
                const isHighlighted = highlightedEvidenceId === item.evidence_id;
                return (
                  <article
                    key={item.evidence_id}
                    className={`rounded-lg border p-4 transition-colors ${
                      isHighlighted
                        ? 'border-indigo-500 bg-indigo-50/60 ring-2 ring-indigo-500/20 dark:border-indigo-400 dark:bg-indigo-950/40'
                        : 'border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-950/50'
                    }`}
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded bg-indigo-600 px-2 py-0.5 font-mono text-[11px] font-semibold text-white">
                          {item.evidence_id}
                        </span>
                        <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                          {item.source_id}
                        </span>
                        {item.access_tier === 'sensitive' && (
                          <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-rose-700 dark:bg-rose-950/70 dark:text-rose-300">
                            Restricted
                          </span>
                        )}
                      </div>

                      {typeof item.relevance_score === 'number' && (
                        <span className="text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
                          Score {(item.relevance_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>

                    <h3 className="flex items-center gap-1.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
                      <FileCheck2 className="h-4 w-4 text-indigo-600" aria-hidden="true" />
                      {item.source_title}
                    </h3>

                    <p className="mt-2 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                      {item.passage}
                    </p>

                    <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-slate-200 pt-2 text-[11px] text-slate-500 dark:border-slate-800 dark:text-slate-400">
                      <span className="font-mono">Ref: {item.retrieval_reference}</span>
                      {item.document_date && (
                        <span className="inline-flex items-center gap-1">
                          <Calendar className="h-3 w-3" aria-hidden="true" />
                          {item.document_date}
                        </span>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
