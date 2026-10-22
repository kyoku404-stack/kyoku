import React, { useState } from 'react';
import type {
  StructuredLogEntry,
  LogLevel,
  LogFilterParams,
} from '@/types/observability';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import {
  FileText,
  Search,
  Filter,
  Clock,
  User,
  Globe,
  Copy,
  Check,
  RefreshCw,
  Terminal,
} from 'lucide-react';

import { formatDate } from '@/utils/formatters';
import { observabilityService } from '@/services/observabilityService';

interface LogViewerProps {
  initialLogs?: StructuredLogEntry[];
  onRefresh?: () => void;
}

export const getLogLevelBadge = (level: LogLevel) => {
  switch (level) {
    case 'CRITICAL':
    case 'ERROR':
      return (
        <Badge variant="destructive" className="font-mono text-[10px] px-1.5 py-0">
          {level}
        </Badge>
      );
    case 'WARN':
      return (
        <Badge variant="warning" className="font-mono text-[10px] px-1.5 py-0">
          {level}
        </Badge>
      );
    case 'INFO':
      return (
        <Badge variant="success" className="font-mono text-[10px] px-1.5 py-0">
          {level}
        </Badge>
      );
    case 'DEBUG':
    default:
      return (
        <Badge variant="secondary" className="font-mono text-[10px] px-1.5 py-0">
          {level}
        </Badge>
      );
  }
};

export const LogViewer: React.FC<LogViewerProps> = ({ initialLogs }) => {
  const [filters, setFilters] = useState<LogFilterParams>({
    query: '',
    level: 'ALL',
    module: 'ALL',
    status: 'ALL',
    requestId: '',
  });

  const [selectedLog, setSelectedLog] = useState<StructuredLogEntry | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [logs, setLogs] = useState<StructuredLogEntry[]>(
    initialLogs || observabilityService.getStructuredLogs()
  );

  const handleRefresh = () => {
    setLogs(observabilityService.getStructuredLogs(filters));
  };

  const handleFilterChange = (key: keyof LogFilterParams, value: string) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);
    setLogs(observabilityService.getStructuredLogs(updated));
  };

  const copyToClipboard = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Terminal className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-semibold">
                  Structured Application Logs & Request Traces
                </CardTitle>
                <Badge variant="secondary" className="text-[10px] font-mono">
                  {logs.length} Entries
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Canonical 13-field enterprise JSON log stream with correlation identifiers and W3C TraceContext.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              className="text-xs h-8 gap-1.5"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5 pt-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search message, user, action..."
              value={filters.query || ''}
              onChange={(e) => handleFilterChange('query', e.target.value)}
              className="pl-8 text-xs h-8"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground shrink-0 flex items-center gap-1">
              <Filter className="h-3 w-3" /> Level:
            </span>
            <select
              value={filters.level}
              onChange={(e) => handleFilterChange('level', e.target.value)}
              className="w-full text-xs h-8 rounded-md border border-input bg-background px-2 text-foreground focus:outline-hidden focus:ring-1 focus:ring-ring"
            >
              <option value="ALL">All Levels</option>
              <option value="INFO">INFO</option>
              <option value="WARN">WARN</option>
              <option value="ERROR">ERROR</option>
              <option value="DEBUG">DEBUG</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground shrink-0">Module:</span>
            <select
              value={filters.module}
              onChange={(e) => handleFilterChange('module', e.target.value)}
              className="w-full text-xs h-8 rounded-md border border-input bg-background px-2 text-foreground focus:outline-hidden focus:ring-1 focus:ring-ring"
            >
              <option value="ALL">All Modules</option>
              <option value="Authentication">Auth Service</option>
              <option value="Document">Document Service</option>
              <option value="AI">AI / RAG Ingestion</option>
              <option value="Storage">Storage Service</option>
              <option value="Database">Database Engine</option>
              <option value="API">API Gateway</option>
            </select>
          </div>

          <div className="relative">
            <Input
              placeholder="Filter by Request ID..."
              value={filters.requestId || ''}
              onChange={(e) => handleFilterChange('requestId', e.target.value)}
              className="text-xs h-8 font-mono"
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 border-t border-border">
        {logs.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm font-medium">No matching structured logs found</p>
            <p className="text-xs mt-1">Try resetting search filters or trigger a backend action.</p>
          </div>
        ) : (
          <div className="divide-y divide-border overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2 px-4">Level</th>
                  <th className="py-2 px-4">Timestamp</th>
                  <th className="py-2 px-4">Module</th>
                  <th className="py-2 px-4">Action</th>
                  <th className="py-2 px-4">Request / Trace ID</th>
                  <th className="py-2 px-4">Duration</th>
                  <th className="py-2 px-4">Status</th>
                  <th className="py-2 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60 font-mono text-[11px]">
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className="hover:bg-muted/30 transition-colors cursor-pointer"
                  >
                    <td className="py-2.5 px-4">{getLogLevelBadge(log.level)}</td>
                    <td className="py-2.5 px-4 text-muted-foreground whitespace-nowrap">
                      <span className="flex items-center gap-1 font-sans">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        {formatDate(log.timestamp)}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-sans font-medium text-foreground whitespace-nowrap">
                      {log.module}
                    </td>
                    <td className="py-2.5 px-4 text-foreground whitespace-nowrap">
                      {log.action}
                    </td>
                    <td className="py-2.5 px-4 text-muted-foreground font-mono text-[10px] whitespace-nowrap">
                      {log.request_id || '--'}
                    </td>
                    <td className="py-2.5 px-4 text-muted-foreground whitespace-nowrap">
                      {log.execution_time_ms !== null && log.execution_time_ms !== undefined ? (
                        <span className="text-foreground font-mono">
                          {log.execution_time_ms.toFixed(1)} ms
                        </span>
                      ) : (
                        '--'
                      )}
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          log.status === 'Success'
                            ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                            : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLog(log);
                        }}
                        className="text-xs text-primary font-sans hover:underline"
                        data-testid={`inspect-log-${log.id}`}
                      >
                        Inspect
                      </button>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>

      {/* Structured Log Detail Modal */}
      {selectedLog && (
        <Modal
          isOpen={!!selectedLog}
          onClose={() => setSelectedLog(null)}
          title="Canonical Structured Log Entry"
          className="max-w-2xl"
        >
          <div className="space-y-4 text-xs font-sans">
            {/* Header badges */}
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                {getLogLevelBadge(selectedLog.level)}
                <span className="font-semibold text-sm text-foreground">
                  {selectedLog.module} — {selectedLog.action}
                </span>
              </div>
              <span
                className={`px-2 py-0.5 rounded font-mono font-semibold text-[11px] ${
                  selectedLog.status === 'Success'
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                }`}
              >
                {selectedLog.status}
              </span>
            </div>

            {/* Message */}
            <div className="bg-muted/40 p-3 rounded-md border border-border">
              <span className="text-[10px] font-semibold uppercase text-muted-foreground block mb-1">
                Log Message
              </span>
              <p className="text-sm text-foreground font-mono">{selectedLog.message}</p>
            </div>

            {/* 13-field metadata grid */}
            <div className="grid grid-cols-2 gap-2.5">
              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <span className="text-[10px] text-muted-foreground block">Timestamp</span>
                <span className="font-mono text-foreground font-medium">
                  {selectedLog.timestamp}
                </span>
              </div>

              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <span className="text-[10px] text-muted-foreground block">Execution Latency</span>
                <span className="font-mono text-foreground font-medium">
                  {selectedLog.execution_time_ms ?? 0} ms
                </span>
              </div>

              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <span className="text-[10px] text-muted-foreground block">User ID / Actor</span>
                <span className="font-mono text-foreground flex items-center gap-1">
                  <User className="h-3 w-3 text-muted-foreground" />
                  {selectedLog.user_id || 'system_worker'}
                </span>
              </div>

              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <span className="text-[10px] text-muted-foreground block">Organization ID</span>
                <span className="font-mono text-foreground">
                  {selectedLog.organization_id || 'system'}
                </span>
              </div>

              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <span className="text-[10px] text-muted-foreground block">Client IP Address</span>
                <span className="font-mono text-foreground flex items-center gap-1">
                  <Globe className="h-3 w-3 text-muted-foreground" />
                  {selectedLog.ip_address || '127.0.0.1'}
                </span>
              </div>

              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <span className="text-[10px] text-muted-foreground block">Request ID</span>
                <div className="flex items-center justify-between font-mono text-foreground">
                  <span>{selectedLog.request_id || '--'}</span>
                  {selectedLog.request_id && (
                    <button
                      onClick={() => copyToClipboard(selectedLog.request_id!, 'req')}
                      className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground"
                      title="Copy Request ID"
                    >
                      {copiedField === 'req' ? (
                        <Check className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* W3C TraceContext */}
            {selectedLog.trace_id && (
              <div className="bg-muted/30 p-2.5 rounded border border-border/60">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold">
                    W3C Traceparent / Trace ID
                  </span>
                  <button
                    onClick={() => copyToClipboard(selectedLog.trace_id!, 'trace')}
                    className="flex items-center gap-1 text-[11px] text-primary hover:underline"
                  >
                    {copiedField === 'trace' ? (
                      <Check className="h-3 w-3 text-emerald-500" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                    <span>Copy Trace ID</span>
                  </button>
                </div>
                <code className="font-mono text-[11px] text-foreground block bg-background/60 p-2 rounded border border-border/40 overflow-x-auto">
                  {selectedLog.trace_id}
                </code>
              </div>
            )}

            {/* Metadata JSON inspection */}
            {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
              <div>
                <span className="text-[10px] font-semibold uppercase text-muted-foreground block mb-1">
                  Structured Event Metadata (JSON)
                </span>
                <pre className="p-3 rounded-md bg-muted/60 border border-border font-mono text-[11px] text-foreground overflow-x-auto max-h-40">
                  {JSON.stringify(selectedLog.metadata, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-border">
              <Button onClick={() => setSelectedLog(null)} variant="outline" size="sm">
                Close Inspector
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </Card>
  );
};

export default LogViewer;
