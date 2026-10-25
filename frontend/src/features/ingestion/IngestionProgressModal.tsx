/**
 * KEEP Enterprise Platform — IngestionProgressModal Component (Phase 2.1).
 *
 * Detailed stage inspector modal displaying real-time execution progress,
 * 8-stage stepper, extracted page counts, vector counts, OCR flags,
 * and error diagnostic analysis with immediate retry capability.
 *
 * Specification: devdocs/p2/p2.1.txt Chapters 14 & 15
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PipelineStageStepper } from './PipelineStageStepper';
import {
  FileText,
  Clock,
  Layers,
  Cpu,
  ScanText,
  RotateCcw,
  AlertTriangle,
  Timer,
  CheckCircle2,
} from 'lucide-react';
import type { IngestionJobStatusResponseData } from '@/types/ingestion';
import { IngestionJobStatus } from '@/types/ingestion';
import { formatDate } from '@/utils/formatters';

interface IngestionProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobStatus: IngestionJobStatusResponseData | null;
  onRetryJob?: (jobId: string) => Promise<void>;
}

export const IngestionProgressModal: React.FC<IngestionProgressModalProps> = ({
  isOpen,
  onClose,
  jobStatus,
  onRetryJob,
}) => {
  if (!jobStatus) return null;

  const isFailed = jobStatus.status === IngestionJobStatus.FAILED;
  const isCompleted = jobStatus.status === IngestionJobStatus.COMPLETED;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AI Ingestion Pipeline Inspector"
      className="max-w-4xl"
    >
      <div className="space-y-6 py-2" data-testid="ingestion-progress-modal">
        {/* Header Summary */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-muted/40 border border-border">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <span className="font-semibold text-foreground text-sm">
                Job ID: <span className="font-mono text-xs text-muted-foreground">{jobStatus.job_id}</span>
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Document Reference: <span className="font-mono">{jobStatus.document_id}</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant={isFailed ? 'destructive' : isCompleted ? 'success' : 'default'}
              className="font-mono text-xs uppercase"
            >
              {jobStatus.status}
            </Badge>
            <Badge variant="outline" className="font-mono text-xs">
              Stage: {jobStatus.current_stage}
            </Badge>
          </div>
        </div>

        {/* Real-time Stepper Visualizer */}
        <div className="p-4 rounded-xl border border-border bg-card">
          <PipelineStageStepper
            currentStage={jobStatus.current_stage}
            status={jobStatus.status}
            progressPercent={jobStatus.progress_percent}
          />
        </div>

        {/* Real-time Processing Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-lg border border-border/60 bg-muted/20">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
              <FileText className="h-3.5 w-3.5 text-primary" /> Pages Processed
            </div>
            <div className="text-lg font-bold text-foreground">
              {jobStatus.processed_pages}{' '}
              <span className="text-xs font-normal text-muted-foreground">
                / {jobStatus.total_pages || '—'}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-border/60 bg-muted/20">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
              <Layers className="h-3.5 w-3.5 text-purple-500" /> Chunks Created
            </div>
            <div className="text-lg font-bold text-foreground">
              {jobStatus.chunks_generated}
            </div>
          </div>

          <div className="p-3 rounded-lg border border-border/60 bg-muted/20">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
              <Cpu className="h-3.5 w-3.5 text-emerald-500" /> Vectors Indexed
            </div>
            <div className="text-lg font-bold text-foreground">
              {jobStatus.embeddings_generated}
            </div>
          </div>

          <div className="p-3 rounded-lg border border-border/60 bg-muted/20">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
              <Timer className="h-3.5 w-3.5 text-amber-500" /> Wall-Clock Time
            </div>
            <div className="text-lg font-bold text-foreground font-mono">
              {jobStatus.duration_seconds.toFixed(2)}s
            </div>
          </div>
        </div>

        {/* Feature Flags & Audit Info */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-muted/30 text-xs text-muted-foreground border border-border/40">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <ScanText className="h-3.5 w-3.5 text-primary" />
              OCR Applied:{' '}
              <span className="font-semibold text-foreground">
                {jobStatus.ocr_applied ? 'Yes (Tesseract/PaddleOCR)' : 'No (Native Text)'}
              </span>
            </span>
            <span className="flex items-center gap-1">
              <RotateCcw className="h-3.5 w-3.5 text-amber-500" />
              Retries:{' '}
              <span className="font-semibold text-foreground">{jobStatus.retry_count}</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {jobStatus.started_at && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" /> Started: {formatDate(jobStatus.started_at)}
              </span>
            )}
          </div>
        </div>

        {/* Error Diagnostic Box */}
        {jobStatus.error_message && (
          <div className="p-4 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-300 space-y-2" data-testid="ingestion-error-box">
            <div className="flex items-center gap-2 font-semibold text-sm">
              <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
              Pipeline Execution Error
            </div>
            <p className="text-xs font-mono bg-background/50 p-2.5 rounded-lg border border-rose-500/20 whitespace-pre-wrap break-all">
              {jobStatus.error_message}
            </p>
          </div>
        )}

        {/* Actions Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <span className="text-xs text-muted-foreground">
            {isCompleted ? (
              <span className="flex items-center gap-1 text-emerald-600 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" /> Vector embeddings ready for AI Search & RAG
              </span>
            ) : isFailed ? (
              <span className="text-rose-500">Processing stopped due to error</span>
            ) : (
              <span className="text-primary animate-pulse">Processing in background queue...</span>
            )}
          </span>

          <div className="flex items-center gap-2">
            {isFailed && onRetryJob && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRetryJob(jobStatus.job_id)}
                className="gap-1.5 border-rose-500/40 text-rose-600 hover:bg-rose-500/10"
                data-testid="modal-retry-btn"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Retry Job
              </Button>
            )}
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default IngestionProgressModal;
