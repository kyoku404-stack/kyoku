/**
 * KEEP Enterprise Platform — Document Preview Modal
 * Phase 1.8: Inline preview for PDF, images, text, and HTML-rendered content.
 */

import React, { useEffect, useState } from 'react';
import {
  X,
  Download,
  ExternalLink,
  Loader2,
  FileText,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  RotateCw,
} from 'lucide-react';
import { documentService } from '@/services/documentService';
import type { DocumentDetail } from '@/types/document';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DocumentPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: DocumentDetail | null;
}

type PreviewMode = 'pdf' | 'image' | 'text' | 'unsupported';

// ─── Helper ───────────────────────────────────────────────────────────────────

function getPreviewMode(fileType: string): PreviewMode {
  if (fileType.includes('pdf')) return 'pdf';
  if (fileType.startsWith('image/') || fileType.includes('png') || fileType.includes('jpeg') || fileType.includes('jpg') || fileType.includes('webp')) return 'image';
  if (fileType.startsWith('text/') || fileType.includes('markdown') || fileType.includes('json') || fileType.includes('csv')) return 'text';
  return 'unsupported';
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ─── Component ────────────────────────────────────────────────────────────────

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  isOpen,
  onClose,
  document,
}) => {
  const [textContent, setTextContent] = useState<string>('');
  const [loadingText, setLoadingText] = useState(false);
  const [imageScale, setImageScale] = useState(1);

  const previewMode = document ? getPreviewMode(document.file_type) : 'unsupported';
  const previewUrl = document ? documentService.getPreviewUrl(document.id) : '';

  // Load text content for text-mode previews
  useEffect(() => {
    if (!isOpen || !document || previewMode !== 'text') return;
    setLoadingText(true);
    const url = documentService.getPreviewUrl(document.id);
    fetch(url, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
    })
      .then((r) => r.text())
      .then((text) => setTextContent(text))
      .catch(() => setTextContent('[Preview not available]'))
      .finally(() => setLoadingText(false));
  }, [isOpen, document, previewMode]);

  // Reset state on open
  useEffect(() => {
    if (isOpen) {
      setImageScale(1);
      setTextContent('');
    }
  }, [isOpen]);

  // Keyboard close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  if (!isOpen || !document) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-md p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Preview: ${document.filename}`}
      id="document-preview-modal"
    >
      <div className="relative flex flex-col w-full max-w-4xl max-h-[92vh] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden">
        {/* ─── Header ─────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border shrink-0 gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <FileText className="h-4 w-4 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground truncate">
                {document.title || document.filename}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatBytes(document.file_size)} · v{document.current_version_number} · {document.status}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {/* Image zoom controls */}
            {previewMode === 'image' && (
              <>
                <button
                  onClick={() => setImageScale((s) => Math.max(0.5, s - 0.25))}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                  title="Zoom out"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-xs text-muted-foreground px-1">{Math.round(imageScale * 100)}%</span>
                <button
                  onClick={() => setImageScale((s) => Math.min(3, s + 0.25))}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                  title="Zoom in"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setImageScale(1)}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                  title="Reset zoom"
                >
                  <RotateCw className="h-4 w-4" />
                </button>
                <div className="w-px h-5 bg-border mx-1" />
              </>
            )}

            {/* Open in new tab */}
            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="h-4 w-4" />
            </a>

            {/* Download */}
            <button
              onClick={() => documentService.downloadDocument(document.id, document.filename)}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
              title="Download"
              id="preview-download-btn"
            >
              <Download className="h-4 w-4" />
            </button>

            {/* Close */}
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition-colors"
              id="preview-close-btn"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* ─── Preview Area ────────────────────────────────────────────── */}
        <div className="flex-1 overflow-auto bg-muted/20 min-h-0">
          {/* PDF Preview */}
          {previewMode === 'pdf' && (
            <iframe
              src={previewUrl}
              className="w-full h-full min-h-[560px] border-0"
              title={`Preview: ${document.filename}`}
              id="preview-pdf-iframe"
            />
          )}

          {/* Image Preview */}
          {previewMode === 'image' && (
            <div className="flex items-center justify-center h-full min-h-[400px] p-6 overflow-auto">
              <img
                src={previewUrl}
                alt={document.filename}
                style={{ transform: `scale(${imageScale})`, transformOrigin: 'center', transition: 'transform 0.2s ease' }}
                className="max-w-full rounded-lg shadow-md"
                id="preview-image"
              />
            </div>
          )}

          {/* Text / Markdown Preview */}
          {previewMode === 'text' && (
            <div className="p-6 h-full min-h-[400px]">
              {loadingText ? (
                <div className="flex items-center justify-center h-32 gap-2 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Loading preview…</span>
                </div>
              ) : (
                <pre
                  id="preview-text-content"
                  className="whitespace-pre-wrap font-mono text-xs text-foreground bg-muted/30 rounded-xl p-5 overflow-auto leading-relaxed"
                >
                  {textContent || '[Empty file]'}
                </pre>
              )}
            </div>
          )}

          {/* Unsupported */}
          {previewMode === 'unsupported' && (
            <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-4 text-muted-foreground p-6">
              <AlertCircle className="h-10 w-10 opacity-50" />
              <div className="text-center">
                <p className="text-sm font-medium">Preview not available</p>
                <p className="text-xs mt-1">
                  This file type ({document.file_type}) cannot be previewed inline.
                </p>
              </div>
              <button
                onClick={() => documentService.downloadDocument(document.id, document.filename)}
                className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Download className="h-4 w-4" />
                Download file
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentPreviewModal;
