/**
 * KEEP Enterprise Platform — IngestionMetricsGrid Component (Phase 2.1).
 *
 * Executive KPI stat cards summarizing pipeline health, throughput velocity,
 * vector indexing volume, OCR utilization, and retry success rates.
 *
 * Specification: devdocs/p2/p2.1.txt Chapter 15 & docs/api/api-contract.md Section 8
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Layers,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Timer,
  ScanText,
  TrendingUp,
} from 'lucide-react';
import type { IngestionStatisticsResponseData } from '@/types/ingestion';

interface IngestionMetricsGridProps {
  statistics: IngestionStatisticsResponseData | null;
  loading?: boolean;
}

export const IngestionMetricsGrid: React.FC<IngestionMetricsGridProps> = ({
  statistics,
  loading = false,
}) => {
  const totalJobs = statistics?.total_jobs ?? 0;
  const completedJobs = statistics?.completed_jobs ?? 0;
  const failedJobs = statistics?.failed_jobs ?? 0;
  const pendingJobs = statistics?.pending_jobs ?? 0;
  const chunksIndexed = statistics?.total_chunks_indexed ?? 0;
  const avgDuration = statistics?.average_duration_seconds ?? 0.0;
  const throughput = statistics?.average_throughput_pages_per_minute ?? 0.0;
  const ocrUtilization = statistics?.ocr_utilization_percent ?? 0.0;
  const retrySuccessRate = statistics?.retry_success_rate_percent ?? 100.0;

  const successRate =
    totalJobs > 0 ? Math.round((completedJobs / totalJobs) * 100) : 100;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="ingestion-metrics-grid">
      {/* 1. Total Jobs & Queue Health */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Ingestion Jobs
          </CardTitle>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Layers className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-bold tracking-tight text-foreground" data-testid="metric-total-jobs">
              {loading ? '—' : totalJobs}
            </div>
            {pendingJobs > 0 && (
              <Badge variant="warning" className="text-[10px] py-0.5">
                {pendingJobs} in queue
              </Badge>
            )}
          </div>
          <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <CheckCircle2 className="h-3 w-3" /> {completedJobs} done
            </span>
            {failedJobs > 0 && (
              <span className="flex items-center gap-1 text-rose-500 font-medium">
                <AlertTriangle className="h-3 w-3" /> {failedJobs} failed
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 2. Total Chunks Indexed */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Vectors & Chunks
          </CardTitle>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-500">
            <Zap className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-bold tracking-tight text-foreground" data-testid="metric-chunks-indexed">
              {loading ? '—' : chunksIndexed.toLocaleString()}
            </div>
            <Badge variant="outline" className="text-[10px] font-mono py-0.5">
              pgvector HNSW
            </Badge>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Semantic vectors indexed for hybrid RAG search
          </p>
        </CardContent>
      </Card>

      {/* 3. Throughput Velocity */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Throughput Velocity
          </CardTitle>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
            <TrendingUp className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-bold tracking-tight text-foreground" data-testid="metric-throughput">
              {loading ? '—' : `${throughput.toFixed(1)}`}
              <span className="text-xs font-normal text-muted-foreground ml-1">pages/min</span>
            </div>
            <Badge variant="success" className="text-[10px] py-0.5">
              {successRate}% pass
            </Badge>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Mean processing duration: <span className="font-semibold text-foreground">{avgDuration.toFixed(1)}s</span>
          </p>
        </CardContent>
      </Card>

      {/* 4. OCR Utilization & Retry Success */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            OCR & Resilience
          </CardTitle>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500">
            <ScanText className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-bold tracking-tight text-foreground" data-testid="metric-ocr-utilization">
              {loading ? '—' : `${ocrUtilization.toFixed(0)}%`}
              <span className="text-xs font-normal text-muted-foreground ml-1">OCR rate</span>
            </div>
            <Badge variant="secondary" className="text-[10px] py-0.5">
              {retrySuccessRate.toFixed(0)}% recovery
            </Badge>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Timer className="h-3 w-3 text-primary" />
            <span>Automatic exponential backoff enabled</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default IngestionMetricsGrid;
