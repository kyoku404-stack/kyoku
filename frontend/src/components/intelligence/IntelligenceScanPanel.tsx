import React, { useState } from 'react';
import type { ScanRequest } from '@/types/proactiveIntelligence';

interface Props {
  actionLoading: boolean;
  onRunScan: (payload: ScanRequest) => void;
}

export const IntelligenceScanPanel: React.FC<Props> = ({ actionLoading, onRunScan }) => {
  const [docTitle, setDocTitle] = useState('Enterprise Data Retention Policy');
  const [prevText, setPrevText] = useState('Customer audit logs must be retained for 90 days.');
  const [currText, setCurrText] = useState('Customer audit logs must be retained for 30 days.');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunScan({
      trigger_source: 'manual',
      suppress_window_seconds: 3600,
      observations: [
        {
          kind: 'document_version',
          document_id: `policy-${Date.now()}`,
          title: docTitle,
          previous_version: 'v1',
          current_version: 'v2',
          previous_content: prevText,
          current_content: currText,
        },
      ],
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      aria-label="Run proactive scan"
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Run Proactive Intelligence Scan
        </h2>
        <button
          type="submit"
          disabled={actionLoading}
          className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {actionLoading ? 'Scanning...' : 'Scan Policy Update'}
        </button>
      </div>
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
        <input
          aria-label="Document title"
          value={docTitle}
          onChange={(e) => setDocTitle(e.target.value)}
          className="rounded border border-slate-300 px-2.5 py-1.5 text-xs dark:border-slate-600 dark:bg-slate-900"
          placeholder="Document title"
        />
        <input
          aria-label="Previous version content"
          value={prevText}
          onChange={(e) => setPrevText(e.target.value)}
          className="rounded border border-slate-300 px-2.5 py-1.5 text-xs dark:border-slate-600 dark:bg-slate-900"
          placeholder="Previous version clause"
        />
        <input
          aria-label="Current version content"
          value={currText}
          onChange={(e) => setCurrText(e.target.value)}
          className="rounded border border-slate-300 px-2.5 py-1.5 text-xs dark:border-slate-600 dark:bg-slate-900"
          placeholder="Current version clause"
        />
      </div>
    </form>
  );
};
