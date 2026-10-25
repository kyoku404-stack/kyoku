/**
 * KEEP Enterprise Platform — AI Knowledge Ingestion Command Center (Phase 2.1).
 *
 * Provides real-time visibility and administrative control over the asynchronous
 * document ingestion, optical character recognition (OCR), semantic chunking,
 * vector embedding generation, and pgvector database indexing engine.
 *
 * Specification: devdocs/p2/p2.1.txt Chapters 15 & 16 & docs/Architecture/ai-ingestion-pipeline.md
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { useIngestion } from '@/hooks/useIngestion';
import {
  IngestionMetricsGrid,
  IngestionJobTable,
  IngestionProgressModal,
  StartIngestionModal,
} from '@/features/ingestion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Cpu,
  RefreshCw,
  Play,
  Layers,
  Sparkles,
  Database,
  ShieldCheck,
  Activity,
  Radio,
  AlertCircle,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const IngestionPage: React.FC = () => {
  const {
    jobs,
    statistics,
    selectedJobStatus,
    loading,
    error,
    lastUpdated,
    isPolling,
    page,
    pageSize,
    totalPages,
    totalJobs,
    statusFilter,
    refresh,
    fetchJobStatus,
    startIngestion,
    retryJob,
    setPage,
    setStatusFilter,
    setSelectedJobStatus,
    togglePolling,
  } = useIngestion({ pollingInterval: 5000 });

  const [inspectModalOpen, setInspectModalOpen] = useState(false);
  const [startModalOpen, setStartModalOpen] = useState(false);

  const handleInspectJob = async (jobId: string) => {
    await fetchJobStatus(jobId);
    setInspectModalOpen(true);
  };

  const handleRetryJob = async (jobId: string) => {
    await retryJob(jobId);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-6 px-4 sm:px-6" id="ingestion-dashboard-page" data-testid="ingestion-page">
      {/* ─── Top Header & Controls ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <Cpu className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                  AI Knowledge Ingestion Pipeline
                </h1>
                <Badge variant="default" className="font-mono text-[10px] py-0.5 px-2 bg-primary/20 text-primary border-primary/30">
                  Phase 2.1
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                Real-time monitoring and orchestration for multimodal document parsing, OCR, semantic chunking, and vector indexing.
              </p>
            </div>
          </div>
        </div>

        {/* Global Action Controls */}
        <div className="flex flex-wrap items-center gap-2 sm:self-center">
          {/* Live Polling Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={togglePolling}
            className="h-9 gap-1.5 text-xs"
            data-testid="toggle-polling-btn"
          >
            <Radio className={isPolling ? 'h-3.5 w-3.5 text-emerald-500 animate-pulse' : 'h-3.5 w-3.5 text-muted-foreground'} />
            {isPolling ? 'Live Polling: ON' : 'Live Polling: OFF'}
          </Button>

          {/* Refresh Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => refresh()}
            disabled={loading}
            className="h-9 gap-1.5 text-xs"
            data-testid="manual-refresh-btn"
          >
            <RefreshCw className={loading ? 'h-3.5 w-3.5 animate-spin' : 'h-3.5 w-3.5'} />
            Refresh
          </Button>

          {/* Trigger Ingestion Button */}
          <Button
            size="sm"
            onClick={() => setStartModalOpen(true)}
            className="h-9 gap-1.5 text-xs shadow-xs"
            data-testid="page-start-ingestion-btn"
          >
            <Play className="h-3.5 w-3.5" /> Start Ingestion
          </Button>
        </div>
      </div>

      {/* ─── Status / Sync Timestamp Banner ───────────────────────────────── */}
      <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
        <div className="flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-emerald-500" />
          <span>Pipeline State: <strong className="text-foreground font-semibold">Active & Healthy</strong></span>
        </div>
        {lastUpdated && (
          <div className="font-mono text-[11px]">
            Last Synced: {formatDate(lastUpdated.toISOString())}
          </div>
        )}
      </div>

      {/* ─── Architecture Overview Pill Card ──────────────────────────────── */}
      <Card className="border-border/70 bg-gradient-to-r from-card via-card to-primary/5 shadow-xs">
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <Sparkles className="h-4 w-4 text-primary" />
                Enterprise Ingestion Engine (ADR-032 / ADR-033 / ADR-034)
              </div>
              <p className="text-xs text-muted-foreground max-w-2xl">
                Uploaded documents automatically flow through a 10-stage asynchronous pipeline. Multi-format parsers handle PDF, DOCX, PPTX, XLSX, and CSV with Tesseract OCR fallback. Text is cleaned, segmented into heading-aware semantic chunks with 10% overlap, and stored in pgvector using HNSW indexing.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5 rounded-lg border border-border bg-background/80 px-2.5 py-1 text-xs">
                <Layers className="h-3.5 w-3.5 text-primary" />
                <span className="font-medium text-foreground">Semantic Chunks</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-lg border border-border bg-background/80 px-2.5 py-1 text-xs">
                <Database className="h-3.5 w-3.5 text-purple-500" />
                <span className="font-medium text-foreground">pgvector HNSW</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-lg border border-border bg-background/80 px-2.5 py-1 text-xs">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                <span className="font-medium text-foreground">Tenant Isolated</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ─── Error Alert ──────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-2 p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ─── Executive KPI Stat Cards ─────────────────────────────────────── */}
      <IngestionMetricsGrid statistics={statistics} loading={loading} />

      {/* ─── Master Ingestion Job History Table ────────────────────────────── */}
      <IngestionJobTable
        jobs={jobs}
        loading={loading}
        page={page}
        pageSize={pageSize}
        totalPages={totalPages}
        totalJobs={totalJobs}
        statusFilter={statusFilter}
        onPageChange={setPage}
        onStatusFilterChange={setStatusFilter}
        onInspectJob={handleInspectJob}
        onRetryJob={handleRetryJob}
        onTriggerStart={() => setStartModalOpen(true)}
      />

      {/* ─── Live Stage Progress Inspector Modal ──────────────────────────── */}
      <IngestionProgressModal
        isOpen={inspectModalOpen}
        onClose={() => {
          setInspectModalOpen(false);
          setSelectedJobStatus(null);
        }}
        jobStatus={selectedJobStatus}
        onRetryJob={handleRetryJob}
      />

      {/* ─── Start Ingestion Config Modal ─────────────────────────────────── */}
      <StartIngestionModal
        isOpen={startModalOpen}
        onClose={() => setStartModalOpen(false)}
        onSubmit={async (payload) => {
          await startIngestion(payload);
        }}
      />
    </div>
  );
};

export default IngestionPage;
