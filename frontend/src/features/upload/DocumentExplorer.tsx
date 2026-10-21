/**
 * KEEP Enterprise Platform — Document Explorer
 * Phase 1.8: Enterprise document browser with card/table views, category tabs,
 * search input, status badges, metadata editing, version upload, and action menus.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Search,
  Grid3X3,
  List,
  UploadCloud,
  Download,
  Eye,
  Edit3,
  Trash2,
  GitBranch,
  MoreVertical,
  Filter,
  RefreshCw,
  FileText,
  FileImage,
  FileSpreadsheet,
  Presentation,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Tag,
  X,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { documentService } from '@/services/documentService';
import type {
  DocumentItem,
  DocumentDetail,
  DocumentListParams,
  DocumentCategory,
  DocumentUpdatePayload,
} from '@/types/document';
import { DOCUMENT_CATEGORIES } from '@/types/document';
import type { PaginatedData } from '@/types/api';
import { DocumentPreviewModal } from './DocumentPreviewModal';
import { VersionHistoryTimeline } from './VersionHistoryTimeline';
import { DocumentUploadModal } from './DocumentUploadModal';

// ─── Types ────────────────────────────────────────────────────────────────────

type ViewMode = 'grid' | 'table';

interface DocumentExplorerProps {
  projectId?: string;
  className?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function getFileIcon(type: string) {
  if (type.includes('pdf') || type.includes('word') || type.includes('text') || type.includes('markdown')) return FileText;
  if (type.includes('image')) return FileImage;
  if (type.includes('sheet') || type.includes('csv')) return FileSpreadsheet;
  if (type.includes('presentation')) return Presentation;
  return FileText;
}

function getStatusColor(status: string) {
  switch (status) {
    case 'PROCESSED': return 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10';
    case 'PROCESSING': return 'text-blue-600 dark:text-blue-400 bg-blue-500/10';
    case 'PENDING':
    case 'AWAITING_PROCESSING': return 'text-amber-600 dark:text-amber-400 bg-amber-500/10';
    case 'FAILED': return 'text-red-600 dark:text-red-400 bg-red-500/10';
    default: return 'text-muted-foreground bg-muted';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'PROCESSED': return CheckCircle2;
    case 'PROCESSING': return Loader2;
    case 'PENDING':
    case 'AWAITING_PROCESSING': return Clock;
    case 'FAILED': return AlertCircle;
    default: return Clock;
  }
}

// ─── Metadata Edit Modal ──────────────────────────────────────────────────────

interface MetadataEditModalProps {
  isOpen: boolean;
  document: DocumentItem | null;
  onClose: () => void;
  onSaved: (updated: DocumentItem) => void;
}

const MetadataEditModal: React.FC<MetadataEditModalProps> = ({ isOpen, document, onClose, onSaved }) => {
  const [form, setForm] = useState<DocumentUpdatePayload>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (document) {
      setForm({
        title: document.title ?? '',
        description: '',
        category: document.category as DocumentCategory,
        tags: document.tags,
      });
    }
  }, [document]);

  const handleSave = async () => {
    if (!document) return;
    setSaving(true);
    setError('');
    try {
      const resp = await documentService.updateMetadata(document.id, form);
      onSaved({ ...document, ...resp.data });
      onClose();
    } catch {
      setError('Failed to update metadata. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4" id="metadata-edit-modal">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card shadow-2xl p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Edit3 className="h-4 w-4 text-primary" />
            Edit Metadata
          </h3>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Title</label>
            <input
              type="text"
              value={form.title ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              id="metadata-title-input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
            <textarea
              rows={2}
              value={form.description ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Category</label>
            <select
              value={form.category ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value as DocumentCategory }))}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              id="metadata-category-select"
            >
              {DOCUMENT_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Tags (comma-separated)</label>
            <input
              type="text"
              value={(form.tags ?? []).join(', ')}
              onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value.split(',').map((t) => t.trim()).filter(Boolean) }))}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              id="metadata-tags-input"
            />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
          <button
            id="metadata-save-btn"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Version Upload Modal ─────────────────────────────────────────────────────

interface VersionUploadModalProps {
  isOpen: boolean;
  document: DocumentItem | null;
  onClose: () => void;
  onVersionUploaded: () => void;
}

const VersionUploadModal: React.FC<VersionUploadModalProps> = ({ isOpen, document, onClose, onVersionUploaded }) => {
  const [file, setFile] = useState<File | null>(null);
  const [changeNotes, setChangeNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    if (!document || !file) return;
    setUploading(true);
    setError('');
    try {
      await documentService.uploadNewVersion(document.id, file, changeNotes || undefined);
      onVersionUploaded();
      onClose();
    } catch {
      setError('Version upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  if (!isOpen || !document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4" id="version-upload-modal">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card shadow-2xl p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-primary" />
            Upload New Version
          </h3>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted">
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-muted-foreground mb-4">
          Current: <span className="font-medium text-foreground">{document.filename}</span> (v{document.version_number})
        </p>
        <div className="space-y-3">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center gap-2 rounded-xl border-2 border-dashed border-border py-6 cursor-pointer hover:border-primary/50 hover:bg-muted/30 transition-colors"
          >
            {file ? (
              <>
                <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                <p className="text-sm font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
              </>
            ) : (
              <>
                <UploadCloud className="h-6 w-6 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">Click to select revised file</p>
              </>
            )}
            <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])} />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Change notes (optional)</label>
            <textarea
              rows={2}
              value={changeNotes}
              onChange={(e) => setChangeNotes(e.target.value)}
              placeholder="Describe what changed in this revision…"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            id="version-upload-submit"
          >
            {uploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <GitBranch className="h-3.5 w-3.5" />}
            {uploading ? 'Uploading…' : 'Upload revision'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Document Card (Grid) ─────────────────────────────────────────────────────

interface DocumentCardProps {
  doc: DocumentItem;
  onPreview: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onNewVersion: () => void;
}

const DocumentCard: React.FC<DocumentCardProps> = ({ doc, onPreview, onEdit, onDelete, onNewVersion }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const Icon = getFileIcon(doc.file_type);
  const StatusIcon = getStatusIcon(doc.status);

  return (
    <div
      className="group relative rounded-xl border border-border bg-card p-4 hover:border-primary/30 hover:shadow-md transition-all duration-200"
      id={`document-card-${doc.id}`}
    >
      {/* File type icon */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        {/* Action menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-8 z-20 min-w-[160px] rounded-xl border border-border bg-card shadow-xl py-1">
                <button onClick={() => { onPreview(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted">
                  <Eye className="h-3.5 w-3.5" /> Preview
                </button>
                <button onClick={() => { documentService.downloadDocument(doc.id, doc.filename); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted">
                  <Download className="h-3.5 w-3.5" /> Download
                </button>
                <button onClick={() => { onEdit(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted">
                  <Edit3 className="h-3.5 w-3.5" /> Edit metadata
                </button>
                <button onClick={() => { onNewVersion(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted">
                  <GitBranch className="h-3.5 w-3.5" /> New version
                </button>
                <div className="h-px bg-border my-1" />
                <button onClick={() => { onDelete(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-500/10">
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Title + filename */}
      <button onClick={onPreview} className="text-left w-full">
        <p className="text-sm font-semibold text-foreground line-clamp-1 hover:text-primary transition-colors">
          {doc.title || doc.filename}
        </p>
        {doc.title && (
          <p className="text-xs text-muted-foreground truncate">{doc.filename}</p>
        )}
      </button>

      {/* Tags */}
      {doc.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {doc.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="flex items-center gap-0.5 rounded-full bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
              <Tag className="h-2.5 w-2.5" />{tag}
            </span>
          ))}
          {doc.tags.length > 3 && (
            <span className="text-[10px] text-muted-foreground">+{doc.tags.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer metadata */}
      <div className="mt-3 flex items-center justify-between">
        <span className={cn('flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold', getStatusColor(doc.status))}>
          <StatusIcon className={cn('h-2.5 w-2.5', doc.status === 'PROCESSING' && 'animate-spin')} />
          {doc.status.replace('_', ' ')}
        </span>
        <span className="text-[10px] text-muted-foreground">{formatBytes(doc.file_size)}</span>
      </div>

      <div className="mt-1.5 flex items-center justify-between text-[10px] text-muted-foreground">
        <span>v{doc.version_number}</span>
        <span>{relativeTime(doc.created_at)}</span>
      </div>

      {/* AI ready badge */}
      {doc.ai_ready && (
        <div className="mt-2 rounded-lg bg-indigo-500/10 px-2 py-1 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 text-center">
          ✦ AI Ready · {doc.chunk_count} chunks
        </div>
      )}
    </div>
  );
};

// ─── Table Row ────────────────────────────────────────────────────────────────

interface TableRowProps {
  doc: DocumentItem;
  onPreview: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onNewVersion: () => void;
}

const DocumentTableRow: React.FC<TableRowProps> = ({ doc, onPreview, onEdit, onDelete, onNewVersion }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const Icon = getFileIcon(doc.file_type);
  const StatusIcon = getStatusIcon(doc.status);

  return (
    <tr className="group border-b border-border hover:bg-muted/20 transition-colors" id={`document-row-${doc.id}`}>
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
            <Icon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <button onClick={onPreview} className="text-sm font-medium text-foreground hover:text-primary truncate block max-w-[200px]">
              {doc.title || doc.filename}
            </button>
            {doc.title && <p className="text-xs text-muted-foreground truncate max-w-[200px]">{doc.filename}</p>}
          </div>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={cn('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold', getStatusColor(doc.status))}>
          <StatusIcon className={cn('h-3 w-3', doc.status === 'PROCESSING' && 'animate-spin')} />
          {doc.status.replace('_', ' ')}
        </span>
      </td>
      <td className="py-3 px-4 text-xs text-muted-foreground">{doc.category.replace('_', ' ')}</td>
      <td className="py-3 px-4 text-xs text-muted-foreground">{formatBytes(doc.file_size)}</td>
      <td className="py-3 px-4 text-xs text-muted-foreground">v{doc.version_number}</td>
      <td className="py-3 px-4 text-xs text-muted-foreground">{relativeTime(doc.created_at)}</td>
      <td className="py-3 px-4">
        <div className="relative flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={onPreview} title="Preview" className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground">
            <Eye className="h-3.5 w-3.5" />
          </button>
          <button onClick={() => documentService.downloadDocument(doc.id, doc.filename)} title="Download" className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground">
            <Download className="h-3.5 w-3.5" />
          </button>
          <div className="relative">
            <button onClick={() => setMenuOpen((o) => !o)} className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground">
              <MoreVertical className="h-3.5 w-3.5" />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-8 z-20 min-w-[150px] rounded-xl border border-border bg-card shadow-xl py-1">
                  <button onClick={() => { onEdit(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-foreground hover:bg-muted">
                    <Edit3 className="h-3 w-3" /> Edit metadata
                  </button>
                  <button onClick={() => { onNewVersion(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-foreground hover:bg-muted">
                    <GitBranch className="h-3 w-3" /> New version
                  </button>
                  <div className="h-px bg-border my-1" />
                  <button onClick={() => { onDelete(); setMenuOpen(false); }} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-500 hover:bg-red-500/10">
                    <Trash2 className="h-3 w-3" /> Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </td>
    </tr>
  );
};

// ─── Main Explorer ─────────────────────────────────────────────────────────────

export const DocumentExplorer: React.FC<DocumentExplorerProps> = ({ projectId, className }) => {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [pagination, setPagination] = useState<Omit<PaginatedData<unknown>, 'items'>>({ total: 0, page: 1, page_size: 20, total_pages: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<DocumentCategory | 'ALL'>('ALL');
  const [page, setPage] = useState(1);

  // Modals
  const [uploadOpen, setUploadOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<DocumentDetail | null>(null);
  const [editDoc, setEditDoc] = useState<DocumentItem | null>(null);
  const [versionDoc, setVersionDoc] = useState<DocumentItem | null>(null);
  const [historyDoc, setHistoryDoc] = useState<DocumentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Debounced search
  const searchDebounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    if (searchDebounce.current) clearTimeout(searchDebounce.current);
    searchDebounce.current = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => { if (searchDebounce.current) clearTimeout(searchDebounce.current); };
  }, [search]);

  // Load documents
  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: DocumentListParams = {
        page,
        page_size: 20,
        search: debouncedSearch || undefined,
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
        project_id: projectId,
      };
      const resp = await documentService.listDocuments(params);
      const paginatedData = resp.data as PaginatedData<DocumentItem>;
      setDocs(paginatedData.items ?? []);
      setPagination({ total: paginatedData.total, page: paginatedData.page, page_size: paginatedData.page_size, total_pages: paginatedData.total_pages });
    } catch {
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, selectedCategory, projectId]);

  useEffect(() => { void loadDocuments(); }, [loadDocuments]);

  const openPreview = async (doc: DocumentItem) => {
    setLoadingDetail(true);
    try {
      const resp = await documentService.getDocumentDetail(doc.id);
      setPreviewDoc(resp.data);
    } catch {
      setError('Could not load document details.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDelete = async (doc: DocumentItem) => {
    if (!confirm(`Delete "${doc.title || doc.filename}"? This cannot be undone.`)) return;
    try {
      await documentService.deleteDocument(doc.id);
      setDocs((prev) => prev.filter((d) => d.id !== doc.id));
    } catch {
      setError('Failed to delete document.');
    }
  };

  const handleMetadataSaved = (updated: DocumentItem) => {
    setDocs((prev) => prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)));
  };

  return (
    <div className={cn('flex flex-col gap-4', className)} id="document-explorer">
      {/* ─── Toolbar ───────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            id="document-search-input"
            type="text"
            placeholder="Search documents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Category filter */}
          <div className="flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 p-1">
            <Filter className="h-3.5 w-3.5 text-muted-foreground ml-1" />
            <select
              id="document-category-filter"
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value as DocumentCategory | 'ALL'); setPage(1); }}
              className="bg-transparent text-xs text-foreground focus:outline-none pr-1"
            >
              <option value="ALL">All categories</option>
              {DOCUMENT_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* View toggle */}
          <div className="flex items-center rounded-lg border border-border bg-muted/40 p-1">
            <button
              id="view-grid-btn"
              onClick={() => setViewMode('grid')}
              className={cn('rounded-md p-1.5 transition-colors', viewMode === 'grid' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground')}
              title="Grid view"
            >
              <Grid3X3 className="h-3.5 w-3.5" />
            </button>
            <button
              id="view-table-btn"
              onClick={() => setViewMode('table')}
              className={cn('rounded-md p-1.5 transition-colors', viewMode === 'table' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground')}
              title="Table view"
            >
              <List className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Refresh */}
          <button
            onClick={loadDocuments}
            disabled={loading}
            className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
            title="Refresh"
            id="document-refresh-btn"
          >
            <RefreshCw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
          </button>

          {/* Upload */}
          <button
            id="document-upload-btn"
            onClick={() => setUploadOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <UploadCloud className="h-4 w-4" />
            Upload
          </button>
        </div>
      </div>

      {/* ─── Stats bar ─────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {loading ? 'Loading…' : `${pagination.total} document${pagination.total !== 1 ? 's' : ''}`}
          {debouncedSearch && ` matching "${debouncedSearch}"`}
        </span>
        <span>Page {pagination.page} of {pagination.total_pages}</span>
      </div>

      {/* ─── Error ─────────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}

      {/* ─── Loading skeleton ───────────────────────────────────────────── */}
      {loading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-border bg-card p-4 animate-pulse">
              <div className="h-10 w-10 rounded-lg bg-muted mb-3" />
              <div className="h-4 w-3/4 rounded bg-muted mb-2" />
              <div className="h-3 w-1/2 rounded bg-muted" />
            </div>
          ))}
        </div>
      )}

      {/* ─── Empty state ────────────────────────────────────────────────── */}
      {!loading && docs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
            <FileText className="h-8 w-8 opacity-40" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-foreground">No documents found</p>
            <p className="text-xs mt-1">
              {debouncedSearch ? `No results for "${debouncedSearch}"` : 'Upload your first document to get started'}
            </p>
          </div>
          <button
            onClick={() => setUploadOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <UploadCloud className="h-4 w-4" />
            Upload documents
          </button>
        </div>
      )}

      {/* ─── Grid View ─────────────────────────────────────────────────── */}
      {!loading && docs.length > 0 && viewMode === 'grid' && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {docs.map((doc) => (
            <DocumentCard
              key={doc.id}
              doc={doc}
              onPreview={() => openPreview(doc)}
              onEdit={() => setEditDoc(doc)}
              onDelete={() => handleDelete(doc)}
              onNewVersion={() => setVersionDoc(doc)}
            />
          ))}
        </div>
      )}

      {/* ─── Table View ────────────────────────────────────────────────── */}
      {!loading && docs.length > 0 && viewMode === 'table' && (
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm" id="documents-table">
            <thead className="bg-muted/50 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="py-3 px-4 text-left">Document</th>
                <th className="py-3 px-4 text-left">Status</th>
                <th className="py-3 px-4 text-left">Category</th>
                <th className="py-3 px-4 text-left">Size</th>
                <th className="py-3 px-4 text-left">Version</th>
                <th className="py-3 px-4 text-left">Uploaded</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {docs.map((doc) => (
                <DocumentTableRow
                  key={doc.id}
                  doc={doc}
                  onPreview={() => openPreview(doc)}
                  onEdit={() => setEditDoc(doc)}
                  onDelete={() => handleDelete(doc)}
                  onNewVersion={() => setVersionDoc(doc)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ─── Pagination ─────────────────────────────────────────────────── */}
      {!loading && pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2" id="document-pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted disabled:opacity-50 transition-colors"
          >
            <ChevronLeft className="h-3.5 w-3.5" /> Previous
          </button>
          {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
            const p = Math.max(1, Math.min(pagination.total_pages - 4, page - 2)) + i;
            return (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={cn(
                  'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                  p === page ? 'bg-primary text-primary-foreground' : 'border border-border text-muted-foreground hover:bg-muted'
                )}
              >
                {p}
              </button>
            );
          })}
          <button
            onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
            disabled={page >= pagination.total_pages}
            className="flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted disabled:opacity-50 transition-colors"
          >
            Next <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* ─── Version History Side Panel ────────────────────────────────── */}
      {historyDoc && (
        <div className="fixed inset-y-0 right-0 z-40 w-full max-w-md flex flex-col border-l border-border bg-card shadow-2xl" id="version-history-panel">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">Version History</h3>
            </div>
            <button onClick={() => setHistoryDoc(null)} className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted">
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-5">
            <VersionHistoryTimeline
              documentId={historyDoc.id}
              documentFilename={historyDoc.filename}
              currentVersionNumber={historyDoc.current_version_number}
              versions={historyDoc.versions}
            />
          </div>
        </div>
      )}

      {/* ─── Loading overlay for detail ────────────────────────────────── */}
      {loadingDetail && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-background/60 backdrop-blur-sm">
          <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-6 py-4 shadow-xl">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm font-medium text-foreground">Loading document…</span>
          </div>
        </div>
      )}

      {/* ─── Modals ─────────────────────────────────────────────────────── */}
      <DocumentUploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        projectId={projectId}
        onUploadsComplete={() => { setUploadOpen(false); void loadDocuments(); }}
      />

      <DocumentPreviewModal
        isOpen={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
        document={previewDoc}
      />

      <MetadataEditModal
        isOpen={!!editDoc}
        document={editDoc}
        onClose={() => setEditDoc(null)}
        onSaved={handleMetadataSaved}
      />

      <VersionUploadModal
        isOpen={!!versionDoc}
        document={versionDoc}
        onClose={() => setVersionDoc(null)}
        onVersionUploaded={() => { setVersionDoc(null); void loadDocuments(); }}
      />
    </div>
  );
};

export default DocumentExplorer;
