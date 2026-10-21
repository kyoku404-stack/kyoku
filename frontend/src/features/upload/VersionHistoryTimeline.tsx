/**
 * KEEP Enterprise Platform — Version History Timeline
 * Phase 1.8: Visual revision history with version numbers, timestamps, uploader info,
 * change notes, and per-version download buttons.
 */

import React from 'react';
import {
  GitBranch,
  Clock,
  Download,
  User,
  FileCheck,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { documentService } from '@/services/documentService';
import type { DocumentVersionItem } from '@/types/document';

// ─── Types ────────────────────────────────────────────────────────────────────

interface VersionHistoryTimelineProps {
  documentId: string;
  documentFilename: string;
  currentVersionNumber: number;
  versions: DocumentVersionItem[];
  className?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ─── Component ────────────────────────────────────────────────────────────────

export const VersionHistoryTimeline: React.FC<VersionHistoryTimelineProps> = ({
  documentId,
  documentFilename,
  currentVersionNumber,
  versions,
  className,
}) => {
  // Sort descending by version number (newest first)
  const sorted = [...versions].sort((a, b) => b.version_number - a.version_number);

  if (sorted.length === 0) {
    return (
      <div className={cn('flex flex-col items-center justify-center py-10 text-muted-foreground', className)}>
        <GitBranch className="h-8 w-8 mb-3 opacity-40" />
        <p className="text-sm">No version history available</p>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)} id="version-history-timeline">
      {/* Timeline vertical line */}
      <div className="absolute left-5 top-6 bottom-6 w-px bg-border" />

      <div className="space-y-4">
        {sorted.map((version, idx) => {
          const isCurrent = version.version_number === currentVersionNumber;
          const isLatest = idx === 0;

          return (
            <div
              key={version.version_number}
              className={cn(
                'relative flex gap-4 rounded-xl border p-4 transition-colors',
                isCurrent
                  ? 'border-primary/40 bg-primary/5'
                  : 'border-border bg-card hover:bg-muted/30'
              )}
              id={`version-item-v${version.version_number}`}
            >
              {/* Timeline dot */}
              <div
                className={cn(
                  'relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold transition-colors',
                  isCurrent
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-border bg-card text-muted-foreground'
                )}
              >
                v{version.version_number}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-foreground">
                        Version {version.version_number}
                      </span>
                      {isCurrent && (
                        <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary">
                          Current
                        </span>
                      )}
                      {isLatest && !isCurrent && (
                        <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                          Latest
                        </span>
                      )}
                    </div>

                    {version.change_notes && (
                      <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1.5">
                        <ChevronRight className="h-3 w-3 shrink-0" />
                        {version.change_notes}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
                      {/* Uploader */}
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <User className="h-3 w-3" />
                        <span className="font-mono text-[10px]">
                          {version.uploader_id.slice(0, 8)}…
                        </span>
                      </span>

                      {/* Size */}
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <FileCheck className="h-3 w-3" />
                        {formatBytes(version.file_size)}
                      </span>

                      {/* Timestamp */}
                      <span
                        className="flex items-center gap-1 text-xs text-muted-foreground"
                        title={formatDate(version.created_at)}
                      >
                        <Clock className="h-3 w-3" />
                        {relativeTime(version.created_at)}
                      </span>

                      {/* Checksum */}
                      <span
                        className="text-[10px] font-mono text-muted-foreground/60"
                        title={`SHA-256: ${version.checksum_sha256}`}
                      >
                        {version.checksum_sha256.slice(0, 10)}…
                      </span>
                    </div>
                  </div>

                  {/* Download this version */}
                  <button
                    onClick={() =>
                      documentService.downloadDocument(
                        documentId,
                        `${documentFilename.replace(/\.[^.]+$/, '')}_v${version.version_number}${documentFilename.includes('.') ? '.' + documentFilename.split('.').pop() : ''}`
                      )
                    }
                    className="shrink-0 flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                    title={`Download version ${version.version_number}`}
                    id={`download-v${version.version_number}`}
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VersionHistoryTimeline;
