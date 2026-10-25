/**
 * KEEP Enterprise Platform — StartIngestionModal Component (Phase 2.1).
 *
 * Modal allowing administrators and engineers to initiate asynchronous ingestion
 * on target documents with custom chunking and embedding configurations.
 *
 * Specification: devdocs/p2/p2.1.txt Chapter 16 & docs/api/api-contract.md Section 8
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  ChunkingStrategy,
  EmbeddingModelProvider,
  type StartIngestionRequest,
} from '@/types/ingestion';
import {
  FileText,
  Cpu,
  Scissors,
  ScanText,
  AlertCircle,
  Play,
  Sparkles,
} from 'lucide-react';

interface StartIngestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: StartIngestionRequest) => Promise<unknown>;
  initialDocumentId?: string;
}

export const StartIngestionModal: React.FC<StartIngestionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialDocumentId = '',
}) => {
  const [documentId, setDocumentId] = useState(initialDocumentId);
  const [forceOcr, setForceOcr] = useState(false);
  const [chunkingStrategy, setChunkingStrategy] = useState<ChunkingStrategy>(
    ChunkingStrategy.SEMANTIC_HEADING_AWARE
  );
  const [targetChunkSize, setTargetChunkSize] = useState<number>(512);
  const [chunkOverlap, setChunkOverlap] = useState<number>(50);
  const [embeddingProvider, setEmbeddingProvider] = useState<EmbeddingModelProvider>(
    EmbeddingModelProvider.OPENAI
  );
  const [embeddingModel, setEmbeddingModel] = useState<string>('text-embedding-3-small');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentId.trim()) {
      setError('Document ID is required to initiate ingestion.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await onSubmit({
        document_id: documentId.trim(),
        force_ocr: forceOcr,
        chunking_strategy: chunkingStrategy,
        target_chunk_size: Number(targetChunkSize),
        chunk_overlap: Number(chunkOverlap),
        embedding_provider: embeddingProvider,
        embedding_model: embeddingModel,
      });
      onClose();
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Failed to trigger ingestion pipeline.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Initiate AI Knowledge Ingestion"
      className="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4 py-2" data-testid="start-ingestion-form">
        <p className="text-xs text-muted-foreground">
          Enqueues the target document for multimodal extraction, optical character recognition (OCR),
          heading-aware semantic chunking, and high-dimensional vector database indexing.
        </p>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Target Document ID */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-primary" /> Target Document UUID
          </label>
          <Input
            data-testid="input-document-id"
            placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6"
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            className="text-xs font-mono"
            required
          />
        </div>

        {/* Chunking Strategy & Sizes */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground flex items-center gap-1">
              <Scissors className="h-3.5 w-3.5 text-purple-500" /> Chunking Strategy
            </label>
            <select
              data-testid="select-chunking-strategy"
              value={chunkingStrategy}
              onChange={(e) => setChunkingStrategy(e.target.value as ChunkingStrategy)}
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:ring-1 focus:ring-primary focus:outline-hidden"
            >
              <option value={ChunkingStrategy.SEMANTIC_HEADING_AWARE}>
                Heading-Aware Semantic
              </option>
              <option value={ChunkingStrategy.FIXED_TOKEN_OVERLAP}>
                Fixed Token Overlap
              </option>
              <option value={ChunkingStrategy.PARAGRAPH_BOUNDARY}>
                Paragraph Boundary
              </option>
              <option value={ChunkingStrategy.HIERARCHICAL_RECURSIVE}>
                Hierarchical Recursive
              </option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">
              Target Size (Tokens)
            </label>
            <Input
              data-testid="input-chunk-size"
              type="number"
              min={64}
              max={4096}
              value={targetChunkSize}
              onChange={(e) => setTargetChunkSize(Number(e.target.value))}
              className="text-xs"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">
              Overlap (Tokens)
            </label>
            <Input
              data-testid="input-chunk-overlap"
              type="number"
              min={0}
              max={512}
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(Number(e.target.value))}
              className="text-xs"
            />
          </div>
        </div>

        {/* Embedding Provider & Model */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground flex items-center gap-1">
              <Cpu className="h-3.5 w-3.5 text-emerald-500" /> Vector Provider
            </label>
            <select
              data-testid="select-embedding-provider"
              value={embeddingProvider}
              onChange={(e) => {
                const val = e.target.value as EmbeddingModelProvider;
                setEmbeddingProvider(val);
                if (val === EmbeddingModelProvider.LOCAL_BGE) {
                  setEmbeddingModel('bge-small-en-v1.5');
                } else {
                  setEmbeddingModel('text-embedding-3-small');
                }
              }}
              className="w-full rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs text-foreground focus:ring-1 focus:ring-primary focus:outline-hidden"
            >
              <option value={EmbeddingModelProvider.OPENAI}>OpenAI Embeddings</option>
              <option value={EmbeddingModelProvider.LOCAL_BGE}>Local BGE (CPU/GPU)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground flex items-center gap-1">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" /> Model Name
            </label>
            <Input
              data-testid="input-embedding-model"
              value={embeddingModel}
              onChange={(e) => setEmbeddingModel(e.target.value)}
              className="text-xs font-mono"
            />
          </div>
        </div>

        {/* Force OCR Checkbox */}
        <div className="flex items-start gap-2 p-3 rounded-lg border border-border/60 bg-muted/20">
          <input
            id="force-ocr-checkbox"
            data-testid="checkbox-force-ocr"
            type="checkbox"
            checked={forceOcr}
            onChange={(e) => setForceOcr(e.target.checked)}
            className="mt-0.5 rounded border-border text-primary focus:ring-primary"
          />
          <label htmlFor="force-ocr-checkbox" className="text-xs text-foreground cursor-pointer">
            <span className="font-semibold flex items-center gap-1">
              <ScanText className="h-3.5 w-3.5 text-primary" /> Force Optical Character Recognition (OCR)
            </span>
            <span className="text-muted-foreground block text-[11px] mt-0.5">
              Execute layout analysis and OCR extraction even on documents that report native text streams (useful for scanned PDFs and diagrams).
            </span>
          </label>
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
          <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" size="sm" disabled={loading} className="gap-1.5" data-testid="submit-ingest-btn">
            <Play className="h-3.5 w-3.5" />
            {loading ? 'Enqueuing Job...' : 'Start Pipeline'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default StartIngestionModal;
