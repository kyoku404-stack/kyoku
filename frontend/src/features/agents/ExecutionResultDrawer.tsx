/**
 * KEEP Enterprise Platform — Phase 4.2 Execution Result & Evidence Inspection Drawer.
 *
 * Slide-over panel displaying validated structured output, grounded EvidenceReference
 * citations, warnings, and sanitized error details for a terminal execution.
 */

import React, { useEffect } from 'react';
import { AlertTriangle, BookOpen, CheckCircle2, X, XCircle } from 'lucide-react';
import type { ExecutionRecordItem, ExecutionResultData } from '@/types/agentRuntime';

interface ExecutionResultDrawerProps {
  execution: ExecutionRecordItem | null;
  result: ExecutionResultData | null;
  loading?: boolean;
  onClose: () => void;
}

export const ExecutionResultDrawer: React.FC<ExecutionResultDrawerProps> = ({
  execution,
  result,
  loading = false,
  onClose,
}) => {
  useEffect(() => {
    if (!execution) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [execution, onClose]);

  if (!execution) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
      aria-label="Execution Result Drawer"
    >
      <div className="bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 w-full max-w-xl h-full flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              Execution Result & Evidence
            </h2>
            <p className="text-xs font-mono text-gray-500 dark:text-gray-400">
              {execution.execution_id} · {execution.agent_id} v{execution.agent_version}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close Drawer"
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metadata Summary */}
          <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 text-xs">
            <div>
              <span className="text-gray-500 dark:text-gray-400 block">Lifecycle Status</span>
              <span className="font-bold text-gray-900 dark:text-white">{execution.status}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400 block">Attempt / Mode</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                #{execution.attempt_number} ({execution.mode.toUpperCase()})
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400 block">Correlation ID</span>
              <span className="font-mono text-gray-800 dark:text-gray-200">
                {execution.correlation_id}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400 block">Duration</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {execution.duration_ms !== null ? `${execution.duration_ms} ms` : '—'}
              </span>
            </div>
          </div>

          {loading ? (
            <div className="p-8 text-center text-sm text-gray-500 dark:text-gray-400">
              Loading validated execution result...
            </div>
          ) : !result ? (
            <div className="p-6 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 text-xs text-amber-800 dark:text-amber-200">
              No result payload is available for this execution.
            </div>
          ) : (
            <>
              {/* Outcome Banner */}
              {result.status === 'succeeded' ? (
                <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 flex items-center gap-2.5 text-xs text-emerald-800 dark:text-emerald-200">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>
                    Validated contract output (schema v{result.schema_version}) persisted durably.
                  </span>
                </div>
              ) : (
                <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-700 flex items-start gap-2.5 text-xs text-rose-800 dark:text-rose-200">
                  <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-bold">
                      {result.error_code || result.error?.code || 'EXECUTION_FAILED'}
                    </div>
                    <p className="mt-0.5">
                      {result.error_message ||
                        result.error?.message ||
                        'Execution terminated with an error.'}
                    </p>
                  </div>
                </div>
              )}

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    Runtime Warnings ({result.warnings.length})
                  </h3>
                  <ul className="space-y-1.5 text-xs text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/60 rounded-xl p-3">
                    {result.warnings.map((warning, idx) => (
                      <li key={idx}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Structured Output Viewer */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-300">
                  Structured Output Payload
                </h3>
                <pre className="p-4 rounded-xl bg-gray-900 text-emerald-300 text-xs font-mono overflow-x-auto max-h-64">
                  {JSON.stringify(result.output, null, 2)}
                </pre>
              </div>

              {/* Grounded Evidence Citations */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-300 flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-indigo-500" />
                  Grounded Evidence Citations ({result.evidence.length})
                </h3>
                {result.evidence.length === 0 ? (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    No external evidence references were attached to this run.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {result.evidence.map((ev, idx) => (
                      <li
                        key={`${ev.source_id}-${idx}`}
                        className="p-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 text-xs"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {ev.title || ev.source_id}
                          </span>
                          <span className="px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 text-[10px] font-semibold uppercase">
                            {ev.source_type}
                          </span>
                        </div>
                        {ev.excerpt && (
                          <p className="mt-1 text-gray-600 dark:text-gray-300">{ev.excerpt}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
