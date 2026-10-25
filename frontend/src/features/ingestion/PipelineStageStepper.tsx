/**
 * KEEP Enterprise Platform — PipelineStageStepper Component (Phase 2.1).
 *
 * Renders an interactive 8-stage visual stepper representing the asynchronous
 * AI Knowledge Ingestion Pipeline:
 * PENDING -> EXTRACTING -> OCR_PROCESSING -> NORMALIZING -> CHUNKING -> EMBEDDING -> INDEXING -> COMPLETED
 *
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import {
  Clock,
  FileText,
  ScanText,
  Sparkles,
  Scissors,
  Cpu,
  Database,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { IngestionJobStatus } from '@/types/ingestion';

export interface StageDefinition {
  key: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const CANONICAL_STAGES: StageDefinition[] = [
  { key: 'PENDING', label: 'Queued', description: 'Worker queue wait', icon: Clock },
  { key: 'EXTRACTING', label: 'Extracting', description: 'Layout & text parsing', icon: FileText },
  { key: 'OCR_PROCESSING', label: 'OCR Engine', description: 'Optical character scan', icon: ScanText },
  { key: 'NORMALIZING', label: 'Normalizing', description: 'NFKC & cleanup', icon: Sparkles },
  { key: 'CHUNKING', label: 'Chunking', description: 'Heading-aware splitting', icon: Scissors },
  { key: 'EMBEDDING', label: 'Embedding', description: 'Vector model synthesis', icon: Cpu },
  { key: 'INDEXING', label: 'Vector Index', description: 'pgvector HNSW store', icon: Database },
  { key: 'COMPLETED', label: 'AI Ready', description: 'Knowledge base indexed', icon: CheckCircle2 },
];

interface PipelineStageStepperProps {
  currentStage: string;
  status: IngestionJobStatus | string;
  progressPercent?: number;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

export const PipelineStageStepper: React.FC<PipelineStageStepperProps> = ({
  currentStage,
  status,
  progressPercent = 0,
  className,
  orientation = 'horizontal',
}) => {
  const isFailed = status === IngestionJobStatus.FAILED;
  const isRetrying = status === IngestionJobStatus.RETRYING;
  const isCompleted = status === IngestionJobStatus.COMPLETED;

  // Determine active index
  const stageKeys = CANONICAL_STAGES.map((s) => s.key);
  let activeIndex = stageKeys.indexOf(currentStage.toUpperCase());
  if (activeIndex === -1) {
    if (isCompleted) activeIndex = stageKeys.length - 1;
    else if (isFailed) activeIndex = 1; // Default highlight
    else activeIndex = 0;
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Top progress indicator */}
      <div className="mb-4 flex items-center justify-between text-xs font-medium text-muted-foreground">
        <span className="flex items-center gap-1.5">
          {isFailed ? (
            <span className="flex items-center gap-1 font-semibold text-rose-500">
              <AlertCircle className="h-4 w-4" /> Pipeline Failed
            </span>
          ) : isRetrying ? (
            <span className="flex items-center gap-1 font-semibold text-amber-500 animate-pulse">
              <RefreshCw className="h-4 w-4 animate-spin" /> Retrying Pipeline
            </span>
          ) : isCompleted ? (
            <span className="flex items-center gap-1 font-semibold text-emerald-500">
              <CheckCircle2 className="h-4 w-4" /> Pipeline Completed
            </span>
          ) : (
            <span className="flex items-center gap-1 text-primary">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Ingestion Active
            </span>
          )}
        </span>
        <span className="font-mono text-sm font-semibold text-foreground">
          {Math.round(progressPercent)}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative mb-6 h-2 w-full overflow-hidden rounded-full bg-muted/60">
        <div
          className={cn(
            'h-full transition-all duration-500 ease-out',
            isFailed
              ? 'bg-rose-500'
              : isCompleted
              ? 'bg-emerald-500'
              : 'bg-primary'
          )}
          style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
        />
      </div>

      {/* Stepper nodes */}
      <div
        className={cn(
          orientation === 'horizontal'
            ? 'grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2'
            : 'flex flex-col gap-3'
        )}
      >
        {CANONICAL_STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isPassed = isCompleted || idx < activeIndex;
          const isCurrent = idx === activeIndex && !isCompleted;

          return (
            <div
              key={stage.key}
              data-testid={`stage-${stage.key.toLowerCase()}`}
              className={cn(
                'flex flex-col items-center rounded-xl p-2.5 text-center transition-all border',
                isCurrent && !isFailed
                  ? 'border-primary/40 bg-primary/5 shadow-xs ring-1 ring-primary/20'
                  : isPassed
                  ? 'border-emerald-500/20 bg-emerald-500/5'
                  : isCurrent && isFailed
                  ? 'border-rose-500/40 bg-rose-500/5 ring-1 ring-rose-500/20'
                  : 'border-border/40 bg-card/40 opacity-70'
              )}
            >
              <div
                className={cn(
                  'mb-2 flex h-8 w-8 items-center justify-center rounded-lg transition-transform',
                  isPassed
                    ? 'bg-emerald-500 text-white'
                    : isCurrent && !isFailed
                    ? 'bg-primary text-primary-foreground animate-pulse'
                    : isCurrent && isFailed
                    ? 'bg-rose-500 text-white'
                    : 'bg-muted text-muted-foreground'
                )}
              >
                {isPassed ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </div>
              <span
                className={cn(
                  'text-xs font-semibold leading-tight line-clamp-1',
                  isCurrent ? 'text-foreground' : isPassed ? 'text-emerald-600 dark:text-emerald-400' : 'text-muted-foreground'
                )}
              >
                {stage.label}
              </span>
              <span className="text-[10px] text-muted-foreground line-clamp-1 mt-0.5">
                {stage.description}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineStageStepper;
