/**
 * Phase 3.1 SyncHistoryTable Component.
 * Audit table displaying resource-level synchronization logs and provenance links.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  FileText,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
  RefreshCw,
  MinusCircle,
  Clock,
} from 'lucide-react';
import type { ConnectorSyncLogItem } from '@/types/connector';

interface HistoryProps {
  logs: ConnectorSyncLogItem[];
  isLoading: boolean;
  onRefresh: () => void;
}

export const SyncHistoryTable: React.FC<HistoryProps> = ({
  logs,
  isLoading,
  onRefresh,
}) => {
  const getActionBadge = (action: string) => {
    switch (action.toUpperCase()) {
      case 'ADDED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            <PlusCircle className="w-3 h-3" /> Added
          </span>
        );
      case 'UPDATED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-400 border border-sky-200 dark:border-sky-800">
            <RefreshCw className="w-3 h-3" /> Updated
          </span>
        );
      case 'DELETED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
            <MinusCircle className="w-3 h-3" /> Deleted
          </span>
        );
      case 'SKIPPED':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
            <Clock className="w-3 h-3" /> Unchanged
          </span>
        );
    }
  };

  const formatTimestamp = (ts: string) => {
    return new Date(ts).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            Synchronization Audit Logs
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Resource-level change detection trail across external enterprise connections.
          </p>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors"
          title="Refresh audit logs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Logs
        </button>
      </div>

      {logs.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400">
          No synchronization logs available yet. Trigger a sync on any connector above to record history.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase font-semibold tracking-wider">
                <th className="py-2.5 px-3">Resource Title</th>
                <th className="py-2.5 px-3">External ID</th>
                <th className="py-2.5 px-3">Delta Action</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Checksum</th>
                <th className="py-2.5 px-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                  {/* Title & Link */}
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2 max-w-xs">
                      <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="font-medium text-slate-900 dark:text-white truncate" title={log.document_title}>
                        {log.document_title}
                      </span>
                      {log.source_url && (
                        <a
                          href={log.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 shrink-0"
                          title="Open external resource"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </td>

                  {/* External ID */}
                  <td className="py-3 px-3 font-mono text-slate-500 dark:text-slate-400">
                    {log.external_document_id}
                  </td>

                  {/* Delta Action */}
                  <td className="py-3 px-3">{getActionBadge(log.action_taken)}</td>

                  {/* Status */}
                  <td className="py-3 px-3">
                    {log.status === 'SUCCESS' ? (
                      <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3 h-3" /> OK
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 font-medium">
                        <AlertCircle className="w-3 h-3" /> Error
                      </span>
                    )}
                  </td>

                  {/* Checksum */}
                  <td className="py-3 px-3 font-mono text-slate-400">
                    {log.checksum ? `${log.checksum.slice(0, 10)}...` : '—'}
                  </td>

                  {/* Timestamp */}
                  <td className="py-3 px-3 text-right text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {formatTimestamp(log.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
