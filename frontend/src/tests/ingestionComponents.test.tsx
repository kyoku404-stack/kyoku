/**
 * KEEP Enterprise Platform — Ingestion UI Components Test Suite (Phase 2.1).
 *
 * Verifies rendering, interactions, accessibility, and state management for:
 * - PipelineStageStepper
 * - IngestionMetricsGrid
 * - IngestionJobTable
 * - IngestionProgressModal
 * - StartIngestionModal
 * - IngestionPage Master Integration
 *
 * Specification: devdocs/p2/p2.1.txt Chapters 15 & 16 & ADR-032 / ADR-033 / ADR-034
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  PipelineStageStepper,
  IngestionMetricsGrid,
  IngestionJobTable,
  IngestionProgressModal,
  StartIngestionModal,
} from '@/features/ingestion';
import { IngestionPage } from '@/pages/IngestionPage';
import { ingestionService } from '@/services/ingestionService';
import {
  IngestionJobStatus,
  ChunkingStrategy,
  EmbeddingModelProvider,
  type IngestionJobListItem,
  type IngestionJobStatusResponseData,
  type IngestionStatisticsResponseData,
} from '@/types/ingestion';

vi.mock('@/services/ingestionService', () => ({
  ingestionService: {
    listIngestionJobs: vi.fn(),
    getIngestionStatistics: vi.fn(),
    getIngestionStatus: vi.fn(),
    startIngestion: vi.fn(),
    retryIngestionJob: vi.fn(),
  },
}));

describe('Phase 2.1 AI Knowledge Ingestion UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('PipelineStageStepper Component', () => {
    it('renders all 8 canonical stages with progress percentage', () => {
      render(
        <PipelineStageStepper
          currentStage="CHUNKING"
          status={IngestionJobStatus.CHUNKING}
          progressPercent={62.5}
        />
      );

      expect(screen.getByText('63%')).toBeInTheDocument();
      expect(screen.getByTestId('stage-pending')).toBeInTheDocument();
      expect(screen.getByTestId('stage-extracting')).toBeInTheDocument();
      expect(screen.getByTestId('stage-ocr_processing')).toBeInTheDocument();
      expect(screen.getByTestId('stage-normalizing')).toBeInTheDocument();
      expect(screen.getByTestId('stage-chunking')).toBeInTheDocument();
      expect(screen.getByTestId('stage-embedding')).toBeInTheDocument();
      expect(screen.getByTestId('stage-indexing')).toBeInTheDocument();
      expect(screen.getByTestId('stage-completed')).toBeInTheDocument();
    });

    it('renders failure state when status is FAILED', () => {
      render(
        <PipelineStageStepper
          currentStage="EXTRACTING"
          status={IngestionJobStatus.FAILED}
          progressPercent={25}
        />
      );

      expect(screen.getByText(/Pipeline Failed/i)).toBeInTheDocument();
    });

    it('renders completion state when status is COMPLETED', () => {
      render(
        <PipelineStageStepper
          currentStage="COMPLETED"
          status={IngestionJobStatus.COMPLETED}
          progressPercent={100}
        />
      );

      expect(screen.getByText(/Pipeline Completed/i)).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('IngestionMetricsGrid Component', () => {
    const mockStats: IngestionStatisticsResponseData = {
      organization_id: 'org-1',
      total_jobs: 88,
      completed_jobs: 80,
      failed_jobs: 4,
      pending_jobs: 4,
      total_chunks_indexed: 3120,
      average_duration_seconds: 4.2,
      average_throughput_pages_per_minute: 95.5,
      ocr_utilization_percent: 22.0,
      retry_success_rate_percent: 92.0,
    };

    it('renders all 4 executive KPI cards with accurate metrics', () => {
      render(<IngestionMetricsGrid statistics={mockStats} loading={false} />);

      expect(screen.getByTestId('metric-total-jobs')).toHaveTextContent('88');
      expect(screen.getByText('4 in queue')).toBeInTheDocument();
      expect(screen.getByText(/80 done/i)).toBeInTheDocument();
      expect(screen.getByText(/4 failed/i)).toBeInTheDocument();
      expect(screen.getByTestId('metric-chunks-indexed')).toHaveTextContent('3,120');
      expect(screen.getByTestId('metric-throughput')).toHaveTextContent('95.5');
      expect(screen.getByTestId('metric-ocr-utilization')).toHaveTextContent('22%');
    });

    it('displays loading placeholders when loading is true', () => {
      render(<IngestionMetricsGrid statistics={null} loading={true} />);

      expect(screen.getByTestId('metric-total-jobs')).toHaveTextContent('—');
      expect(screen.getByTestId('metric-chunks-indexed')).toHaveTextContent('—');
    });
  });

  describe('IngestionJobTable Component', () => {
    const mockJobs: IngestionJobListItem[] = [
      {
        job_id: 'job-1111-2222-3333-4444',
        document_id: 'doc-1',
        document_title: 'Executive Financial Summary.pdf',
        status: IngestionJobStatus.COMPLETED,
        chunks_generated: 48,
        duration_seconds: 3.5,
        created_at: '2026-10-25T11:00:00Z',
        completed_at: '2026-10-25T11:00:04Z',
      },
      {
        job_id: 'job-5555-6666-7777-8888',
        document_id: 'doc-2',
        document_title: 'Engineering Technical Blueprint.docx',
        status: IngestionJobStatus.FAILED,
        chunks_generated: 0,
        duration_seconds: 1.2,
        created_at: '2026-10-25T11:15:00Z',
        completed_at: null,
      },
    ];

    it('renders table rows, document titles, status badges, and chunks', () => {
      render(
        <IngestionJobTable
          jobs={mockJobs}
          loading={false}
          page={1}
          pageSize={10}
          totalPages={1}
          totalJobs={2}
          statusFilter={null}
          onPageChange={vi.fn()}
          onStatusFilterChange={vi.fn()}
          onInspectJob={vi.fn()}
          onRetryJob={vi.fn()}
        />
      );

      expect(screen.getByText('Executive Financial Summary.pdf')).toBeInTheDocument();
      expect(screen.getByText('Engineering Technical Blueprint.docx')).toBeInTheDocument();
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('FAILED')).toBeInTheDocument();
      expect(screen.getByText('48 chunks')).toBeInTheDocument();
    });

    it('filters rows dynamically using the search bar input', () => {
      render(
        <IngestionJobTable
          jobs={mockJobs}
          loading={false}
          page={1}
          pageSize={10}
          totalPages={1}
          totalJobs={2}
          statusFilter={null}
          onPageChange={vi.fn()}
          onStatusFilterChange={vi.fn()}
          onInspectJob={vi.fn()}
          onRetryJob={vi.fn()}
        />
      );

      const searchInput = screen.getByTestId('ingestion-search-input');
      fireEvent.change(searchInput, { target: { value: 'Financial' } });

      expect(screen.getByText('Executive Financial Summary.pdf')).toBeInTheDocument();
      expect(screen.queryByText('Engineering Technical Blueprint.docx')).not.toBeInTheDocument();
    });

    it('triggers onInspectJob callback when clicking Inspect button', () => {
      const handleInspect = vi.fn();
      render(
        <IngestionJobTable
          jobs={mockJobs}
          loading={false}
          page={1}
          pageSize={10}
          totalPages={1}
          totalJobs={2}
          statusFilter={null}
          onPageChange={vi.fn()}
          onStatusFilterChange={vi.fn()}
          onInspectJob={handleInspect}
          onRetryJob={vi.fn()}
        />
      );

      const inspectBtn = screen.getByTestId('inspect-btn-job-1111-2222-3333-4444');
      fireEvent.click(inspectBtn);

      expect(handleInspect).toHaveBeenCalledWith('job-1111-2222-3333-4444');
    });

    it('displays Retry button on failed jobs and invokes onRetryJob', async () => {
      const handleRetry = vi.fn().mockResolvedValue(undefined);
      render(
        <IngestionJobTable
          jobs={mockJobs}
          loading={false}
          page={1}
          pageSize={10}
          totalPages={1}
          totalJobs={2}
          statusFilter={null}
          onPageChange={vi.fn()}
          onStatusFilterChange={vi.fn()}
          onInspectJob={vi.fn()}
          onRetryJob={handleRetry}
        />
      );

      const retryBtn = screen.getByTestId('retry-btn-job-5555-6666-7777-8888');
      expect(retryBtn).toBeInTheDocument();

      fireEvent.click(retryBtn);
      expect(handleRetry).toHaveBeenCalledWith('job-5555-6666-7777-8888');
    });

    it('invokes onStatusFilterChange when clicking filter tabs', () => {
      const handleFilter = vi.fn();
      render(
        <IngestionJobTable
          jobs={mockJobs}
          loading={false}
          page={1}
          pageSize={10}
          totalPages={1}
          totalJobs={2}
          statusFilter={null}
          onPageChange={vi.fn()}
          onStatusFilterChange={handleFilter}
          onInspectJob={vi.fn()}
          onRetryJob={vi.fn()}
        />
      );

      const failedTab = screen.getByTestId('filter-tab-failed');
      fireEvent.click(failedTab);

      expect(handleFilter).toHaveBeenCalledWith(IngestionJobStatus.FAILED);
    });
  });

  describe('IngestionProgressModal Component', () => {
    const mockJobStatus: IngestionJobStatusResponseData = {
      job_id: 'job-999',
      document_id: 'doc-888',
      status: IngestionJobStatus.CHUNKING,
      progress_percent: 62.5,
      current_stage: 'CHUNKING',
      total_pages: 15,
      processed_pages: 15,
      chunks_generated: 42,
      embeddings_generated: 0,
      ocr_applied: true,
      retry_count: 0,
      error_message: null,
      started_at: '2026-10-25T11:00:00Z',
      completed_at: null,
      duration_seconds: 4.8,
    };

    it('renders modal details, stages, and metrics when open', () => {
      render(
        <IngestionProgressModal
          isOpen={true}
          onClose={vi.fn()}
          jobStatus={mockJobStatus}
        />
      );

      expect(screen.getByTestId('ingestion-progress-modal')).toBeInTheDocument();
      expect(screen.getByText('Job ID:')).toBeInTheDocument();
      expect(screen.getByText('job-999')).toBeInTheDocument();
      expect(screen.getByText(/Pages Processed/i)).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText(/Yes \(Tesseract\/PaddleOCR\)/i)).toBeInTheDocument();
    });

    it('renders error diagnostic box when error_message is present', () => {
      const errorJobStatus: IngestionJobStatusResponseData = {
        ...mockJobStatus,
        status: IngestionJobStatus.FAILED,
        current_stage: 'OCR_PROCESSING',
        error_message: 'Corrupted image stream in page 3 of scanned document',
      };

      render(
        <IngestionProgressModal
          isOpen={true}
          onClose={vi.fn()}
          jobStatus={errorJobStatus}
          onRetryJob={vi.fn()}
        />
      );

      expect(screen.getByTestId('ingestion-error-box')).toBeInTheDocument();
      expect(
        screen.getByText('Corrupted image stream in page 3 of scanned document')
      ).toBeInTheDocument();
      expect(screen.getByTestId('modal-retry-btn')).toBeInTheDocument();
    });
  });

  describe('StartIngestionModal Component', () => {
    it('renders configuration inputs and submits valid payload', async () => {
      const handleSubmit = vi.fn().mockResolvedValue({ success: true });
      const handleClose = vi.fn();

      render(
        <StartIngestionModal
          isOpen={true}
          onClose={handleClose}
          onSubmit={handleSubmit}
          initialDocumentId="doc-test-123"
        />
      );

      expect(screen.getByTestId('start-ingestion-form')).toBeInTheDocument();
      const docInput = screen.getByTestId('input-document-id');
      expect(docInput).toHaveValue('doc-test-123');

      const forceOcrCheckbox = screen.getByTestId('checkbox-force-ocr');
      fireEvent.click(forceOcrCheckbox);

      const submitBtn = screen.getByTestId('submit-ingest-btn');
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(handleSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            document_id: 'doc-test-123',
            force_ocr: true,
            chunking_strategy: ChunkingStrategy.SEMANTIC_HEADING_AWARE,
            target_chunk_size: 512,
            chunk_overlap: 50,
            embedding_provider: EmbeddingModelProvider.OPENAI,
          })
        );
        expect(handleClose).toHaveBeenCalled();
      });
    });
  });

  describe('IngestionPage Master Integration', () => {
    it('renders complete Ingestion Command Center and triggers refresh', async () => {
      vi.mocked(ingestionService.listIngestionJobs).mockResolvedValue({
        success: true,
        message: 'OK',
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          total_pages: 1,
        },
      });

      vi.mocked(ingestionService.getIngestionStatistics).mockResolvedValue({
        success: true,
        message: 'OK',
        data: {
          organization_id: 'org-1',
          total_jobs: 12,
          completed_jobs: 10,
          failed_jobs: 1,
          pending_jobs: 1,
          total_chunks_indexed: 540,
          average_duration_seconds: 3.1,
          average_throughput_pages_per_minute: 88.0,
          ocr_utilization_percent: 15.0,
          retry_success_rate_percent: 100.0,
        },
      });

      render(
        <MemoryRouter>
          <IngestionPage />
        </MemoryRouter>
      );

      expect(screen.getByTestId('ingestion-page')).toBeInTheDocument();
      expect(
        screen.getByRole('heading', { name: /AI Knowledge Ingestion Pipeline/i })
      ).toBeInTheDocument();
      expect(screen.getByText('Phase 2.1')).toBeInTheDocument();
      expect(
        screen.getByText(/Enterprise Ingestion Engine \(ADR-032 \/ ADR-033 \/ ADR-034\)/i)
      ).toBeInTheDocument();

      const refreshBtn = screen.getByTestId('manual-refresh-btn');
      fireEvent.click(refreshBtn);

      await waitFor(() => {
        expect(ingestionService.listIngestionJobs).toHaveBeenCalled();
        expect(ingestionService.getIngestionStatistics).toHaveBeenCalled();
      });
    });
  });
});
