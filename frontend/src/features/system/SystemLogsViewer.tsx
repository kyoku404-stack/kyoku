/**
 * KEEP Enterprise Platform — Centralized System Logs Viewer.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Filter,
  Info,
  RefreshCw,
  Search,
  Terminal,
} from 'lucide-react';
import type { LogSeverity, SystemLogEntryData } from '@/types/system';

interface SystemLogsViewerProps {
  logs: SystemLogEntryData[];
  onRefresh: (params?: { service_name?: string; severity?: string; query?: string }) => void;
  loading: boolean;
}

export const SystemLogsViewer: React.FC<SystemLogsViewerProps> = ({
  logs,
  onRefresh,
  loading,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedService, setSelectedService] = useState<string>('ALL');
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const severities: (LogSeverity | 'ALL')[] = ['ALL', 'INFO', 'WARN', 'ERROR', 'FATAL'];

  const services = [
    'ALL',
    'keep-backend-api',
    'keep-frontend',
    'keep-ai-worker',
    'keep-ingestion-worker',
    'keep-embedding-worker',
    'keep-notification-srv',
    'keep-scheduler',
    'keep-deployment-orchestrator',
    'keep-disaster-recovery',
  ];

  const handleApplyFilter = () => {
    onRefresh({
      service_name: selectedService !== 'ALL' ? selectedService : undefined,
      severity: selectedSeverity !== 'ALL' ? selectedSeverity : undefined,
      query: searchQuery.trim() || undefined,
    });
  };

  const getSeverityBadge = (sev: LogSeverity) => {
    switch (sev) {
      case 'INFO':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Info className="w-3 h-3" />
            INFO
          </span>
        );
      case 'WARN':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" />
            WARN
          </span>
        );
      case 'ERROR':
      case 'FATAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" />
            {sev}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300">
            {sev}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md mb-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Terminal className="w-5 h-5 text-indigo-400" />
            Centralized Operational Logs
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Structured JSON log aggregation from all containerized nodes and background microservices.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleApplyFilter()}
              placeholder="Search log messages..."
              className="bg-slate-800 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-48 sm:w-60"
            />
          </div>

          {/* Service Dropdown */}
          <select
            value={selectedService}
            onChange={(e) => {
              setSelectedService(e.target.value);
              onRefresh({
                service_name: e.target.value !== 'ALL' ? e.target.value : undefined,
                severity: selectedSeverity !== 'ALL' ? selectedSeverity : undefined,
                query: searchQuery.trim() || undefined,
              });
            }}
            className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {services.map((s) => (
              <option key={s} value={s}>
                {s === 'ALL' ? 'All Services' : s}
              </option>
            ))}
          </select>

          {/* Refresh Button */}
          <button
            type="button"
            onClick={handleApplyFilter}
            disabled={loading}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl border border-slate-700 transition-colors"
            title="Refresh logs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Severity Filter Pills */}
      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1">
        <span className="text-xs text-slate-400 flex items-center gap-1 shrink-0">
          <Filter className="w-3.5 h-3.5" /> Severity:
        </span>
        {severities.map((sev) => (
          <button
            key={sev}
            type="button"
            onClick={() => {
              setSelectedSeverity(sev);
              onRefresh({
                service_name: selectedService !== 'ALL' ? selectedService : undefined,
                severity: sev !== 'ALL' ? sev : undefined,
                query: searchQuery.trim() || undefined,
              });
            }}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              selectedSeverity === sev
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Log Feed List */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-800/80 font-mono text-xs">
        {logs.length === 0 ? (
          <div className="py-8 text-center text-slate-500">
            No system logs found matching the filter criteria.
          </div>
        ) : (
          logs.map((log) => {
            const isExpanded = expandedLogId === log.id;
            return (
              <div key={log.id} className="hover:bg-slate-900/60 transition-colors">
                <div
                  className="p-3 flex items-start gap-3 cursor-pointer select-none"
                  onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                >
                  <button type="button" className="text-slate-500 mt-0.5">
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5" />
                    )}
                  </button>

                  <span className="text-slate-500 shrink-0 text-[11px] mt-0.5">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>

                  <div className="shrink-0">{getSeverityBadge(log.severity)}</div>

                  <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 text-[11px] shrink-0 border border-slate-800">
                    {log.service_name}
                  </span>

                  <span className="text-slate-200 flex-1 truncate font-sans text-xs">
                    {log.message}
                  </span>

                  {log.trace_id && (
                    <span className="text-slate-500 text-[11px] shrink-0 hidden sm:inline" title="Trace ID">
                      {log.trace_id}
                    </span>
                  )}
                </div>

                {/* Expanded Diagnostic Metadata */}
                {isExpanded && (
                  <div className="px-9 pb-3 pt-1 bg-slate-900/40 text-[11px] text-slate-400">
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 overflow-x-auto">
                      <pre className="text-slate-300">
                        {JSON.stringify(
                          {
                            log_id: log.id,
                            service: log.service_name,
                            severity: log.severity,
                            trace_id: log.trace_id,
                            timestamp: log.created_at,
                            metadata: log.metadata,
                          },
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

