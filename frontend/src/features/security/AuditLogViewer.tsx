/**
 * Phase 3.3 AuditLogViewer Component.
 * Searchable, filterable immutable enterprise audit trail with detailed JSON payload inspector
 * and compliance export capabilities.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  Eye,
  X,
  ChevronLeft,
  ChevronRight,
  Download,
} from 'lucide-react';
import type { SecurityAuditLogItem } from '@/types/security';
import type { AuditLogQueryParams } from '@/services/securityService';

interface AuditLogViewerProps {
  logs: SecurityAuditLogItem[];
  total: number;
  page: number;
  pageSize?: number;
  onFetchLogs: (params?: AuditLogQueryParams) => void;
  onExport: (format: 'json' | 'csv') => void;
  isLoading: boolean;
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({
  logs,
  total,
  page,
  pageSize = 20,
  onFetchLogs,
  onExport,
  isLoading,
}) => {
  const [actionQuery, setActionQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [activeLogDetail, setActiveLogDetail] = useState<SecurityAuditLogItem | null>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onFetchLogs({
      page: 1,
      page_size: pageSize,
      action: actionQuery.trim() || undefined,
      status: selectedStatus || undefined,
    });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage < 1) return;
    onFetchLogs({
      page: newPage,
      page_size: pageSize,
      action: actionQuery.trim() || undefined,
      status: selectedStatus || undefined,
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            SUCCESS
          </span>
        );
      case 'FAILURE':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
            <AlertOctagon className="w-3 h-3 text-amber-500" />
            FAILURE
          </span>
        );
      case 'DENIED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
            <XCircle className="w-3 h-3 text-rose-500" />
            DENIED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
            {status}
          </span>
        );
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex flex-col gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-5">
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            Immutable Audit Trail
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Tamper-evident cryptographically sequenced enterprise activity records
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Filter by action..."
              value={actionQuery}
              onChange={(e) => setActionQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
          </div>

          <div className="flex items-center gap-1 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg px-2 py-1">
            <Filter className="w-3 h-3 text-slate-400" />
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                onFetchLogs({
                  page: 1,
                  page_size: pageSize,
                  action: actionQuery.trim() || undefined,
                  status: e.target.value || undefined,
                });
              }}
              className="text-xs bg-transparent text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="SUCCESS">Success</option>
              <option value="FAILURE">Failure</option>
              <option value="DENIED">Denied</option>
            </select>
          </div>

          <button
            type="submit"
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-teal-600 hover:bg-teal-700 text-white transition shadow-sm"
          >
            Apply
          </button>

          <div className="flex items-center gap-1 border-l border-slate-200 dark:border-slate-700 pl-2">
            <button
              type="button"
              onClick={() => onExport('csv')}
              className="p-1.5 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition"
              title="Export as CSV"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Timestamp</th>
              <th className="py-2.5 px-3">Action</th>
              <th className="py-2.5 px-3">Resource</th>
              <th className="py-2.5 px-3">IP Address</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400">
                  {isLoading ? 'Loading audit records...' : 'No audit records found matching criteria.'}
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr
                  key={log.id}
                  className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition"
                >
                  <td className="py-2.5 px-3 font-mono text-slate-500 dark:text-slate-400 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-slate-800 dark:text-slate-200">
                    {log.action}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-600 dark:text-slate-400">
                    {log.resource} {log.resource_id ? `(${log.resource_id.slice(0, 8)}...)` : ''}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-500">
                    {log.ip_address}
                  </td>
                  <td className="py-2.5 px-3">
                    {getStatusBadge(log.status)}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => setActiveLogDetail(log)}
                      className="inline-flex items-center gap-1 text-teal-600 dark:text-teal-400 hover:underline font-medium"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400">
        <div>
          Showing {logs.length} of {total} records (Page {page} of {totalPages})
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1 || isLoading}
            className="p-1 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
            className="p-1 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* JSON Payload Inspector Modal */}
      {activeLogDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-900 dark:text-white">
                  Audit Record Inspector: {activeLogDetail.action}
                </span>
                {getStatusBadge(activeLogDetail.status)}
              </div>
              <button
                onClick={() => setActiveLogDetail(null)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh] flex flex-col gap-3 font-mono text-xs">
              <div className="grid grid-cols-2 gap-2 p-2 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800">
                <div><span className="text-slate-400">ID:</span> {activeLogDetail.id}</div>
                <div><span className="text-slate-400">Time:</span> {activeLogDetail.created_at}</div>
                <div><span className="text-slate-400">IP:</span> {activeLogDetail.ip_address}</div>
                <div><span className="text-slate-400">Resource:</span> {activeLogDetail.resource}</div>
              </div>
              <div>
                <p className="text-slate-400 mb-1 font-sans font-semibold">Structured Audit Details</p>
                <pre className="p-3 bg-slate-950 text-emerald-400 rounded-lg overflow-x-auto text-[11px] leading-relaxed border border-slate-800">
                  {JSON.stringify(activeLogDetail.details, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogViewer;
