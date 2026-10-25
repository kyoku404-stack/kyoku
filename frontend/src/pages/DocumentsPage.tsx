/**
 * KEEP Enterprise Platform — Documents Page
 * Phase 1.8: Enterprise knowledge repository — upload, browse, preview, and manage documents.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderOpen,
  UploadCloud,
  Layers,
  Shield,
  Zap,
  ChevronRight,
  Cpu,
} from 'lucide-react';
import { DocumentExplorer } from '@/features/upload/DocumentExplorer';
import { DocumentUploadModal } from '@/features/upload/DocumentUploadModal';
import { useAuthorization } from '@/hooks/useAuthorization';
import { Permission } from '@/types/permission';

// ─── Page ─────────────────────────────────────────────────────────────────────

export const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [uploadOpen, setUploadOpen] = useState(false);
  const { can } = useAuthorization();
  const canUpload = can(Permission.DOCUMENT_CREATE);

  return (
    <div className="flex flex-col gap-6 p-6 max-w-screen-2xl mx-auto" id="documents-page">
      {/* ─── Page Header ─────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
            <FolderOpen className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Knowledge Repository</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Upload, organize, and manage your enterprise documents. Files are automatically queued for AI ingestion.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            id="view-ingestion-btn"
            data-testid="view-ingestion-btn"
            onClick={() => navigate('/ingestion')}
            className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-semibold text-foreground hover:bg-muted/50 shadow-xs transition-colors"
          >
            <Cpu className="h-4 w-4 text-primary" />
            AI Ingestion Pipeline
          </button>

          {canUpload && (
            <button
              id="page-upload-btn"
              onClick={() => setUploadOpen(true)}
              className="flex shrink-0 items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 shadow-xs transition-colors"
            >
              <UploadCloud className="h-4 w-4" />
              Upload Documents
            </button>
          )}
        </div>
      </div>

      {/* ─── Feature Pills ────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-2">
        {[
          { icon: Layers, label: 'Multi-format support', sub: 'PDF, DOCX, PPTX, XLSX, TXT, MD, images' },
          { icon: Shield, label: 'Secure storage', sub: 'SHA-256 checksums · Org-isolated' },
          { icon: Zap, label: 'AI-ready pipeline', sub: 'Auto-queued for ingestion in Phase 2' },
        ].map(({ icon: Icon, label, sub }) => (
          <div key={label} className="flex items-center gap-2 rounded-full border border-border bg-muted/30 px-3 py-1.5">
            <Icon className="h-3.5 w-3.5 text-primary" />
            <span className="text-xs font-medium text-foreground">{label}</span>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">{sub}</span>
          </div>
        ))}
      </div>

      {/* ─── Document Explorer ────────────────────────────────────────── */}
      <DocumentExplorer />

      {/* ─── Upload Modal ─────────────────────────────────────────────── */}
      <DocumentUploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploadsComplete={() => setUploadOpen(false)}
      />
    </div>
  );
};

export default DocumentsPage;
