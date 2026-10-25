/**
 * KEEP Enterprise Platform — IngestionJobTable Component (Phase 2.1).
 *
 * Filterable, paginated table listing all active and historical ingestion runs.
 * Provides quick inspection triggers, real-time status badges, and one-click retry actions.
 *
 * Specification: devdocs/p2/p2.1.txt Chapter 15 & docs/api/api-contract.md Section 8
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Search,
  RefreshCw,
  Eye,
  AlertCircle,
  CheckCircle2,
  Clock,
  RotateCcw,
  FileText,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react';
import { IngestionJobStatus, type IngestionJobListItem } from '@/types/ingestion';
import { formatDate } from '@/utils/formatters';
import { cn } from '@/utils/cn';

interface IngestionJobTableProps {
  jobs: IngestionJobListItem[];
  loading?: boolean;
  page: number;
  pageSize: number;
  totalPages: number;
  totalJobs: number;
  statusFilter: string | null;
  onPageChange: (newPage: number) => void;
  onStatusFilterChange: (status: string | null) => void;
  onInspectJob: (jobId: string) => void;
  onRetryJob: (jobId: string) => Promise<void>;
  onTriggerStart?: () => void;
}

export const IngestionJobTable: React.FC<IngestionJobTableProps> = ({
  jobs,
  loading = false,
  page,
  totalPages,
  totalJobs,
  statusFilter,
  onPageChange,
  onStatusFilterChange,
  onInspectJob,
  onRetryJob,
  onTriggerStart,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [retryingJobId, setRetryingJobId] = useState<string | null>(null);

  // Client-side search filtering by document title or job_id
  const filteredJobs = useMemo(() => {
    if (!searchQuery.trim()) return jobs;
    const q = searchQuery.toLowerCase();
    return jobs.filter(
      (j) =>
        j.document_title.toLowerCase().includes(q) ||
        j.job_id.toLowerCase().includes(q) ||
        j.document_id.toLowerCase().includes(q)
    );
  }, [jobs, searchQuery]);

  const handleRetry = async (jobId: string) => {
    try {
      setRetryingJobId(jobId);
      await onRetryJob(jobId);
    } finally {
      setRetryingJobId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === IngestionJobStatus.COMPLETED) {
      return (
        <Badge variant="success" className="gap-1 font-mono text-[10px]">
          <CheckCircle2 className="h-3 w-3" /> COMPLETED
        </Badge>
      );
    }
    if (s === IngestionJobStatus.FAILED) {
      return (
        <Badge variant="destructive" className="gap-1 font-mono text-[10px]">
          <AlertCircle className="h-3 w-3" /> FAILED
        </Badge>
      );
    }
    if (s === IngestionJobStatus.RETRYING) {
      return (
        <Badge variant="warning" className="gap-1 font-mono text-[10px] animate-pulse">
          <RotateCcw className="h-3 w-3 animate-spin" /> RETRYING
        </Badge>
      );
    }
    if (s === IngestionJobStatus.PENDING) {
      return (
        <Badge variant="secondary" className="gap-1 font-mono text-[10px]">
          <Clock className="h-3 w-3" /> PENDING
        </Badge>
      );
    }
    // Any active intermediate stage (EXTRACTING, OCR, NORMALIZING, CHUNKING, EMBEDDING, INDEXING)
    return (
      <Badge variant="default" className="gap-1 font-mono text-[10px] animate-pulse">
        <RefreshCw className="h-3 w-3 animate-spin" /> {s}
      </Badge>
    );
  };

  const filterTabs = [
    { label: 'All Jobs', value: null },
    { label: 'In Progress', value: 'PROCESSING' },
    { label: 'Completed', value: IngestionJobStatus.COMPLETED },
    { label: 'Failed', value: IngestionJobStatus.FAILED },
  ];

  return (
    <Card className="border-border bg-card shadow-xs" data-testid="ingestion-job-table">
      <CardHeader className="flex flex-col gap-4 border-b border-border sm:flex-row sm:items-center sm:justify-between pb-4">
        <div>
          <CardTitle className="text-base font-semibold text-foreground flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            Ingestion Pipeline Execution Log
          </CardTitle>
          <p className="text-xs text-muted-foreground mt-0.5">
            Real-time tracking of document parsing, semantic chunking, and vector indexing runs ({totalJobs} total recorded)
          </p>
        </div>

        {/* Tab Filters */}
        <div className="flex flex-wrap items-center gap-1.5 rounded-xl bg-muted/50 p-1 border border-border/60">
          {filterTabs.map((tab) => {
            const active = statusFilter === tab.value;
            return (
              <button
                key={tab.label}
                data-testid={`filter-tab-${tab.label.toLowerCase().replace(/\s+/g, '-')}`}
                onClick={() => onStatusFilterChange(tab.value)}
                className={cn(
                  'rounded-lg px-3 py-1.5 text-xs font-medium transition-all',
                  active
                    ? 'bg-card text-foreground shadow-xs font-semibold'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Search controls */}
        <div className="flex items-center justify-between gap-4 p-4 border-b border-border/60 bg-muted/10">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              data-testid="ingestion-search-input"
              placeholder="Search by document title or job ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>
          {onTriggerStart && (
            <Button
              size="sm"
              onClick={onTriggerStart}
              className="gap-1.5 text-xs"
              data-testid="start-new-ingestion-btn"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Start Ingestion
            </Button>
          )}
        </div>

        {/* Jobs Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-muted/30 text-muted-foreground uppercase text-[10px] font-semibold tracking-wider">
              <tr>
                <th className="py-3 px-4">Document Title</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Chunks</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Created At</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {loading && jobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-muted-foreground">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-primary" />
                    Loading ingestion pipeline runs...
                  </td>
                </tr>
              ) : filteredJobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                        <Filter className="h-6 w-6" />
                      </div>
                      <p className="text-sm font-semibold text-foreground">No ingestion jobs found</p>
                      <p className="text-xs text-muted-foreground max-w-sm">
                        {searchQuery
                          ? 'No jobs match your current search query.'
                          : 'No document ingestion runs recorded under this filter.'}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredJobs.map((job) => {
                  const isRetrying = retryingJobId === job.job_id;
                  const isFailed = job.status === IngestionJobStatus.FAILED;

                  return (
                    <tr
                      key={job.job_id}
                      data-testid={`job-row-${job.job_id}`}
                      className="hover:bg-muted/30 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-foreground max-w-xs truncate">
                          {job.document_title || 'Untitled Document'}
                        </div>
                        <div className="font-mono text-[10px] text-muted-foreground truncate">
                          ID: {job.job_id.slice(0, 8)}...
                        </div>
                      </td>
                      <td className="py-3 px-4">{getStatusBadge(job.status)}</td>
                      <td className="py-3 px-4 font-mono font-medium text-foreground">
                        {job.chunks_generated > 0 ? (
                          <span className="flex items-center gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-purple-500 inline-block" />
                            {job.chunks_generated} chunks
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-muted-foreground">
                        {job.duration_seconds > 0 ? `${job.duration_seconds.toFixed(2)}s` : '—'}
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onInspectJob(job.job_id)}
                            className="h-8 px-2 text-xs gap-1"
                            title="Inspect Stage Progress"
                            data-testid={`inspect-btn-${job.job_id}`}
                          >
                            <Eye className="h-3.5 w-3.5" />
                            Inspect
                          </Button>

                          {isFailed && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRetry(job.job_id)}
                              disabled={isRetrying}
                              className="h-8 px-2 text-xs gap-1 border-rose-500/40 text-rose-600 hover:bg-rose-500/10"
                              title="Retry Ingestion Job"
                              data-testid={`retry-btn-${job.job_id}`}
                            >
                              <RotateCcw
                                className={cn('h-3.5 w-3.5', isRetrying && 'animate-spin')}
                              />
                              Retry
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-card">
            <span className="text-xs text-muted-foreground">
              Page <span className="font-semibold text-foreground">{page}</span> of{' '}
              <span className="font-semibold text-foreground">{totalPages}</span>
            </span>
            <div className="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                className="h-8 px-2.5 text-xs gap-1"
                data-testid="pagination-prev"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                className="h-8 px-2.5 text-xs gap-1"
                data-testid="pagination-next"
              >
                Next <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IngestionJobTable;
