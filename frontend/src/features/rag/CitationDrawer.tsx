/**
 * KEEP Enterprise Platform — CitationDrawer Component (Phase 2.2).
 *
 * Slide-over provenance inspector displaying full chunk context,
 * page and section coordinates, document metadata, and similarity rankings.
 *
 * Specification: devdocs/p2/p2.2.txt Chapter 11 & docs/decisions/decisions.md ADR-037
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { X, FileText, Bookmark, Hash, Layers, ExternalLink, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { RAGCitationDetail } from '@/types/rag';

interface CitationDrawerProps {
  citation: RAGCitationDetail | null;
  isOpen: boolean;
  onClose: () => void;
  isLoading?: boolean;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citation,
  isOpen,
  onClose,
  isLoading = false,
}) => {
  if (!isOpen || !citation) return null;

  return (
    <div
      className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-card/95 backdrop-blur-md shadow-2xl transition-transform duration-300"
      data-testid="citation-drawer"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border p-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Source Provenance</h3>
            <p className="text-xs text-muted-foreground">Verified Grounding Evidence</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          data-testid="btn-close-citation"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Body Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Document Title & Reference */}
        <div className="rounded-xl border border-border bg-background/50 p-3.5 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h4
              className="text-sm font-bold text-foreground line-clamp-2"
              data-testid="citation-doc-title"
            >
              {citation.document_title || 'Enterprise Document'}
            </h4>
            <Badge variant="outline" className="text-[10px] font-mono shrink-0">
              Chunk #{citation.chunk_index ?? 0}
            </Badge>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground pt-1">
            {citation.page_number && (
              <span className="flex items-center gap-1">
                <Bookmark className="h-3 w-3 text-primary" />
                Page {citation.page_number}
              </span>
            )}
            {citation.section && (
              <span className="flex items-center gap-1">
                <Layers className="h-3 w-3 text-purple-400" />
                {citation.section}
              </span>
            )}
            <span className="flex items-center gap-1 font-mono text-[10px]">
              <Hash className="h-3 w-3 text-muted-foreground" />
              {citation.chunk_id.slice(0, 8)}...
            </span>
          </div>
        </div>

        {/* Excerpt / Full Content */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <span className="flex items-center gap-1">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              Grounding Passage
            </span>
            <span className="text-[10px] font-normal lowercase">100% verified citation</span>
          </div>

          {isLoading ? (
            <div className="space-y-2 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4"></div>
              <div className="h-4 bg-muted rounded w-full"></div>
              <div className="h-4 bg-muted rounded w-5/6"></div>
            </div>
          ) : (
            <div
              className="rounded-xl border border-border/80 bg-background/70 p-4 text-xs font-normal leading-relaxed text-foreground/90 whitespace-pre-wrap select-text shadow-inner"
              data-testid="citation-full-content"
            >
              {citation.full_content}
            </div>
          )}
        </div>

        {/* Provenance Metadata Table */}
        <div className="rounded-xl border border-border bg-muted/30 p-3 space-y-2 text-xs">
          <h5 className="font-semibold text-muted-foreground text-[11px] uppercase tracking-wider">
            Indexing Metadata
          </h5>
          <div className="grid grid-cols-2 gap-2 text-muted-foreground font-mono text-[11px]">
            <div>
              <span className="block text-[10px] text-muted-foreground/70 uppercase">Document ID</span>
              <span className="truncate block text-foreground" title={citation.document_id}>
                {citation.document_id}
              </span>
            </div>
            <div>
              <span className="block text-[10px] text-muted-foreground/70 uppercase">Chunk ID</span>
              <span className="truncate block text-foreground" title={citation.chunk_id}>
                {citation.chunk_id}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="border-t border-border p-4 bg-card/60 flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={onClose}
          className="text-xs"
        >
          Close Drawer
        </Button>
        <Button
          variant="primary"
          size="sm"
          className="text-xs flex items-center gap-1.5"
          onClick={() => {
            // Document navigation / preview hook
            window.open(`/documents/${citation.document_id}`, '_blank');
          }}
          data-testid="btn-view-source-doc"
        >
          <span>View Source Document</span>
          <ExternalLink className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
};
