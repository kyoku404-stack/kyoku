/**
 * KEEP Enterprise Platform — Document Upload Modal
 * Phase 1.8: Drag-and-drop file uploader with validation, metadata form, and progress tracking.
 */

import React, { useCallback, useRef, useState } from 'react';
import {
  X,
  UploadCloud,
  FileText,
  FileImage,
  FileSpreadsheet,
  Presentation,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { documentService } from '@/services/documentService';
import type {
  DocumentCategory,
  DocumentUploadResponse,
} from '@/types/document';
import {
  SUPPORTED_EXTENSIONS,
  MAX_FILE_SIZES,
  DOCUMENT_CATEGORIES as CATEGORIES,
} from '@/types/document';

// ─── Types ────────────────────────────────────────────────────────────────────

type UploadStatus = 'pending' | 'uploading' | 'success' | 'error';

interface QueuedFile {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  error?: string;
  result?: DocumentUploadResponse;
  title: string;
  description: string;
  category: DocumentCategory;
  tags: string;
}

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadsComplete?: (results: DocumentUploadResponse[]) => void;
  projectId?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getFileIcon(type: string) {
  if (type.includes('pdf') || type.includes('word') || type.includes('text')) {
    return FileText;
  }
  if (type.includes('image')) return FileImage;
  if (type.includes('sheet') || type.includes('csv')) return FileSpreadsheet;
  if (type.includes('presentation')) return Presentation;
  return FileText;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateFile(file: File): string | null {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!SUPPORTED_EXTENSIONS.includes(ext)) {
    return `Unsupported file type: ${ext}. Allowed: ${SUPPORTED_EXTENSIONS.join(', ')}`;
  }
  const maxSize = MAX_FILE_SIZES[file.type] ?? MAX_FILE_SIZES['default'];
  if (file.size > maxSize) {
    return `File too large: ${formatBytes(file.size)}. Maximum: ${formatBytes(maxSize)}`;
  }
  return null;
}

// ─── Component ────────────────────────────────────────────────────────────────

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadsComplete,
  projectId,
}) => {
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const newEntries: QueuedFile[] = [];
    Array.from(files).forEach((file) => {
      const error = validateFile(file);
      newEntries.push({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        file,
        status: error ? 'error' : 'pending',
        progress: 0,
        error: error ?? undefined,
        title: file.name.replace(/\.[^.]+$/, ''),
        description: '',
        category: 'REPORTS',
        tags: '',
      });
    });
    setQueue((prev) => [...prev, ...newEntries]);
  }, []);

  // ─── Drag & Drop handlers ──────────────────────────────────────────────────

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files);
  };
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) addFiles(e.target.files);
    e.target.value = '';
  };

  // ─── Queue management ─────────────────────────────────────────────────────

  const updateEntry = (id: string, patch: Partial<QueuedFile>) => {
    setQueue((prev) => prev.map((q) => (q.id === id ? { ...q, ...patch } : q)));
  };

  const removeEntry = (id: string) => {
    setQueue((prev) => prev.filter((q) => q.id !== id));
  };

  // ─── Upload all pending ────────────────────────────────────────────────────

  const handleUploadAll = async () => {
    const pending = queue.filter((q) => q.status === 'pending');
    if (!pending.length) return;
    setIsUploading(true);

    const results: DocumentUploadResponse[] = [];

    await Promise.all(
      pending.map(async (entry) => {
        updateEntry(entry.id, { status: 'uploading', progress: 10 });
        try {
          const resp = await documentService.uploadDocument(entry.file, {
            title: entry.title || undefined,
            description: entry.description || undefined,
            category: entry.category,
            tags: entry.tags ? entry.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
            project_id: projectId,
          });
          updateEntry(entry.id, { status: 'success', progress: 100, result: resp.data });
          results.push(resp.data);
        } catch (err: unknown) {
          const msg =
            err instanceof Error ? err.message : 'Upload failed. Please try again.';
          updateEntry(entry.id, { status: 'error', progress: 0, error: msg });
        }
      })
    );

    setIsUploading(false);
    if (results.length > 0) onUploadsComplete?.(results);
  };

  const pendingCount = queue.filter((q) => q.status === 'pending').length;
  const successCount = queue.filter((q) => q.status === 'success').length;

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Upload Documents"
      id="document-upload-modal"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden">
        {/* ─── Header ────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
              <UploadCloud className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Upload Documents</h2>
              <p className="text-xs text-muted-foreground">
                PDF, DOCX, PPTX, XLSX, TXT, MD, CSV, PNG, JPG · Max 100MB
              </p>
            </div>
          </div>
          <button
            id="upload-modal-close"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* ─── Drop Zone ─────────────────────────────────────────────────── */}
        <div className="px-6 pt-5 shrink-0">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'group relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed py-8 px-6 cursor-pointer transition-all duration-200',
              isDragging
                ? 'border-primary bg-primary/5 scale-[0.99]'
                : 'border-border hover:border-primary/50 hover:bg-muted/40'
            )}
            id="upload-drop-zone"
          >
            <div
              className={cn(
                'flex h-12 w-12 items-center justify-center rounded-full transition-colors',
                isDragging ? 'bg-primary/20' : 'bg-muted group-hover:bg-primary/10'
              )}
            >
              <UploadCloud
                className={cn('h-6 w-6 transition-colors', isDragging ? 'text-primary' : 'text-muted-foreground group-hover:text-primary')}
              />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-foreground">
                {isDragging ? 'Drop files here' : 'Drag & drop files, or click to browse'}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Supported: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV, images
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={SUPPORTED_EXTENSIONS.join(',')}
              className="hidden"
              onChange={handleFileInput}
              id="upload-file-input"
            />
          </div>
        </div>

        {/* ─── Queue ─────────────────────────────────────────────────────── */}
        {queue.length > 0 && (
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 min-h-0">
            {queue.map((entry) => {
              const Icon = getFileIcon(entry.file.type);
              return (
                <div
                  key={entry.id}
                  className={cn(
                    'rounded-xl border p-4 transition-colors',
                    entry.status === 'success'
                      ? 'border-emerald-500/30 bg-emerald-500/5'
                      : entry.status === 'error'
                        ? 'border-red-500/30 bg-red-500/5'
                        : entry.status === 'uploading'
                          ? 'border-primary/30 bg-primary/5'
                          : 'border-border bg-muted/20'
                  )}
                >
                  {/* File header */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {entry.file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">{formatBytes(entry.file.size)}</p>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {entry.status === 'success' && (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      )}
                      {entry.status === 'uploading' && (
                        <Loader2 className="h-4 w-4 text-primary animate-spin" />
                      )}
                      {entry.status === 'error' && (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                      {entry.status !== 'uploading' && entry.status !== 'success' && (
                        <button
                          onClick={() => removeEntry(entry.id)}
                          className="rounded-md p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors"
                          title="Remove"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Upload progress */}
                  {entry.status === 'uploading' && (
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden mb-3">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-300"
                        style={{ width: `${entry.progress}%` }}
                      />
                    </div>
                  )}

                  {/* Error message */}
                  {entry.error && entry.status === 'error' && (
                    <p className="text-xs text-red-500 mb-3">{entry.error}</p>
                  )}

                  {/* Success result */}
                  {entry.status === 'success' && entry.result && (
                    <p className="text-xs text-emerald-600 dark:text-emerald-400">
                      ✓ Uploaded — status: {entry.result.status}
                    </p>
                  )}

                  {/* Metadata form — only for pending */}
                  {entry.status === 'pending' && (
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      <input
                        type="text"
                        placeholder="Title (optional)"
                        value={entry.title}
                        onChange={(e) => updateEntry(entry.id, { title: e.target.value })}
                        className="col-span-2 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                      <select
                        value={entry.category}
                        onChange={(e) => updateEntry(entry.id, { category: e.target.value as DocumentCategory })}
                        className="rounded-lg border border-border bg-background px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        {CATEGORIES.map((c) => (
                          <option key={c.value} value={c.value}>{c.label}</option>
                        ))}
                      </select>
                      <input
                        type="text"
                        placeholder="Tags (comma-separated)"
                        value={entry.tags}
                        onChange={(e) => updateEntry(entry.id, { tags: e.target.value })}
                        className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ─── Footer ────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-muted/20 shrink-0">
          <div className="text-xs text-muted-foreground">
            {queue.length > 0
              ? `${successCount} uploaded · ${pendingCount} pending · ${queue.filter((q) => q.status === 'error').length} failed`
              : 'No files selected'}
          </div>
          <div className="flex items-center gap-2">
            {queue.length > 0 && (
              <button
                onClick={() => setQueue([])}
                disabled={isUploading}
                className="rounded-lg px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
                id="upload-clear-all"
              >
                Clear all
              </button>
            )}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-muted-foreground border border-border hover:bg-muted transition-colors"
              id="upload-add-more"
            >
              <Plus className="h-3.5 w-3.5" />
              Add more
            </button>
            <button
              id="upload-submit-btn"
              onClick={handleUploadAll}
              disabled={isUploading || pendingCount === 0}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Uploading…
                </>
              ) : (
                <>
                  <UploadCloud className="h-3.5 w-3.5" />
                  Upload {pendingCount > 0 ? `${pendingCount} file${pendingCount > 1 ? 's' : ''}` : ''}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUploadModal;
