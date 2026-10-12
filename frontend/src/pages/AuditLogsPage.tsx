import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { auditService } from '@/services/auditService';
import type { AuditLogEntry } from '@/types/audit';
import { useAuthorization } from '@/hooks/useAuthorization';
import { Permission } from '@/types/permission';
import {
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Clock,
  Filter,
  FileText,
  ChevronLeft,
  ChevronRight,
  Database,
  Search,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const AuditLogsPage: React.FC = () => {
  const { can, role } = useAuthorization();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [resourceFilter, setResourceFilter] = useState<string>('all');

  const hasAuditPermission = can(Permission.AUDIT_READ);

  const fetchLogs = useCallback(async () => {
    if (!hasAuditPermission) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await auditService.getAuditLogs({
        page,
        page_size: 15,
        action: actionFilter !== 'all' ? actionFilter : undefined,
        resource_type: resourceFilter !== 'all' ? resourceFilter : undefined,
      });

      if (response.success && response.data) {
        setLogs(response.data.items);
        setTotalPages(response.data.total_pages || 1);
        setTotalCount(response.data.total);
      } else {
        setError('Failed to load audit logs.');
      }
    } catch (err: unknown) {
      // In offline / unit test mock mode or if backend responds with simulated items
      setError(err instanceof Error ? err.message : 'Error fetching audit logs');
    } finally {
      setLoading(false);
    }
  }, [hasAuditPermission, page, actionFilter, resourceFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const getActionBadge = (action: string) => {
    if (action.includes('DENIED') || action.includes('REVOKE') || action.includes('DELETE')) {
      return (
        <Badge variant="destructive" className="gap-1 font-mono text-[10px]">
          <ShieldAlert className="h-3 w-3" />
          {action}
        </Badge>
      );
    }
    if (action.includes('GRANTED') || action.includes('CREATE') || action.includes('LOGIN')) {
      return (
        <Badge variant="success" className="gap-1 font-mono text-[10px]">
          <ShieldCheck className="h-3 w-3" />
          {action}
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="gap-1 font-mono text-[10px]">
        {action}
      </Badge>
    );
  };

  if (!hasAuditPermission) {
    return (
      <div className="container mx-auto max-w-5xl px-4 py-8">
        <Card className="border-destructive/30 bg-card p-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
            <ShieldAlert className="h-7 w-7" />
          </div>
          <CardTitle className="text-xl">Audit Log Access Restricted</CardTitle>
          <CardDescription className="max-w-md mx-auto mt-2">
            Viewing the security audit trail requires the <code className="font-mono font-semibold">audit.read</code> permission (assigned to Organization Administrators). Your active role is <span className="font-semibold">{role}</span>.
          </CardDescription>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Security Audit Trail
            </h1>
            <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
              Phase 1.6 RBAC
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Immutable organizational audit log tracking permission grants, denials, and resource mutations.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchLogs}
          disabled={loading}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Log
        </Button>
      </div>

      {/* Filter Bar */}
      <Card className="p-4 bg-card/60 backdrop-blur-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Filter className="h-3.5 w-3.5" />
            <span>Filter Events:</span>
          </div>

          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="h-8 rounded-md border border-border bg-background px-2.5 text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            aria-label="Filter by action"
          >
            <option value="all">All Actions</option>
            <option value="PERMISSION_GRANTED">PERMISSION_GRANTED</option>
            <option value="PERMISSION_DENIED">PERMISSION_DENIED</option>
            <option value="AUTH_LOGIN">AUTH_LOGIN</option>
            <option value="DOCUMENT_UPLOAD">DOCUMENT_UPLOAD</option>
            <option value="DOCUMENT_DELETE">DOCUMENT_DELETE</option>
          </select>

          <select
            value={resourceFilter}
            onChange={(e) => {
              setResourceFilter(e.target.value);
              setPage(1);
            }}
            className="h-8 rounded-md border border-border bg-background px-2.5 text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            aria-label="Filter by resource type"
          >
            <option value="all">All Resources</option>
            <option value="document">Document</option>
            <option value="project">Project</option>
            <option value="department">Department</option>
            <option value="team">Team</option>
            <option value="organization">Organization</option>
            <option value="analytics">Analytics</option>
          </select>

          <div className="ml-auto text-xs text-muted-foreground">
            <span>Total Events: </span>
            <span className="font-semibold text-foreground">{totalCount}</span>
          </div>
        </div>
      </Card>

      {/* Logs Table */}
      <Card className="overflow-hidden">
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <LoadingSpinner size="lg" label="Loading security audit records..." />
          </div>
        ) : error && logs.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground space-y-3">
            <Database className="mx-auto h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm">{error}</p>
            <Button size="sm" variant="outline" onClick={fetchLogs}>
              Try Again
            </Button>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground space-y-2">
            <Search className="mx-auto h-8 w-8 text-muted-foreground/40" />
            <p className="text-base font-semibold text-foreground">No Audit Events Found</p>
            <p className="text-xs">No matching authorization activity records found with current filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-muted/40 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Event Action</th>
                  <th className="py-3 px-4">Resource Domain</th>
                  <th className="py-3 px-4">Details & Reason</th>
                  <th className="py-3 px-4">Client IP</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {logs.map((entry) => (
                  <tr key={entry.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap">
                      {getActionBadge(entry.action)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {entry.resource_type ? (
                        <span className="inline-flex items-center gap-1.5 text-xs text-foreground font-medium">
                          <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="capitalize">{entry.resource_type}</span>
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 max-w-xs sm:max-w-md truncate text-xs text-muted-foreground">
                      {entry.details || 'No additional details'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap font-mono text-xs text-muted-foreground">
                      {entry.ip_address || '127.0.0.1'}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5" />
                        <span>{formatDate(entry.created_at)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-muted/20">
            <div className="text-xs text-muted-foreground">
              Page <span className="font-semibold text-foreground">{page}</span> of{' '}
              <span className="font-semibold text-foreground">{totalPages}</span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="h-8 gap-1 text-xs"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="h-8 gap-1 text-xs"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
