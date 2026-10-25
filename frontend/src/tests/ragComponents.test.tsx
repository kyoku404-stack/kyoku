/**
 * KEEP Enterprise Platform — RAG UI Components Test Suite (Phase 2.2).
 *
 * Verifies rendering, interactions, accessibility, and state management for:
 * - RAGMetricsBanner
 * - SearchFilterBar
 * - CitationDrawer
 * - SessionHistorySidebar
 * - ChatThread
 * - RAGChatPage Master Integration
 *
 * Specification: devdocs/p2/p2.2.txt Chapters 11, 12, 13, 15, 17 & ADR-035/036/037
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  RAGMetricsBanner,
  SearchFilterBar,
  CitationDrawer,
  SessionHistorySidebar,
  ChatThread,
} from '@/features/rag';
import { RAGChatPage } from '@/pages/RAGChatPage';
import { ragService } from '@/services/ragService';
import type {
  RAGStatistics,
  RAGCitationDetail,
  RAGChatSessionItem,
  RAGChatMessageItem,
  RAGQueryResponse,
} from '@/types/rag';

vi.mock('@/services/ragService', () => ({
  ragService: {
    queryRAG: vi.fn(),
    getHistory: vi.fn(),
    getCitationDetail: vi.fn(),
    submitFeedback: vi.fn(),
    getStatistics: vi.fn(),
  },
}));

describe('Phase 2.2 AI Knowledge Search & RAG UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('RAGMetricsBanner Component', () => {
    const mockStats: RAGStatistics = {
      organization_id: 'org-test',
      total_queries: 520,
      total_sessions: 110,
      average_latency_ms: 320.4,
      average_confidence_score: 0.885,
      hallucination_refusal_count: 12,
      positive_feedback_percentage: 96.2,
      total_citations_rendered: 1560,
      cache_hit_ratio: 0.35,
    };

    it('renders all 5 KPI cards with formatted metrics', () => {
      render(<RAGMetricsBanner statistics={mockStats} loading={false} />);

      expect(screen.getByTestId('metric-total-queries')).toHaveTextContent('520');
      expect(screen.getByTestId('metric-avg-latency')).toHaveTextContent('320 ms');
      expect(screen.getByTestId('metric-mean-confidence')).toHaveTextContent('88.5%');
      expect(screen.getByTestId('metric-satisfaction')).toHaveTextContent('96.2%');
      expect(screen.getByTestId('metric-refusals')).toHaveTextContent('12');
    });

    it('displays loading dash indicators when loading is true', () => {
      render(<RAGMetricsBanner statistics={null} loading={true} />);

      expect(screen.getByTestId('metric-total-queries')).toHaveTextContent('—');
      expect(screen.getByTestId('metric-avg-latency')).toHaveTextContent('—');
    });
  });

  describe('SearchFilterBar Component', () => {
    it('handles slider adjustments, candidate top_k change, and preset buttons', () => {
      const setDense = vi.fn();
      const setSparse = vi.fn();
      const setTopK = vi.fn();

      render(
        <SearchFilterBar
          hybridDenseWeight={0.65}
          setHybridDenseWeight={setDense}
          hybridSparseWeight={0.35}
          setHybridSparseWeight={setSparse}
          topK={5}
          setTopK={setTopK}
        />
      );

      // Verify preset buttons exist
      const balancedBtn = screen.getByTestId('preset-balanced');
      const semanticBtn = screen.getByTestId('preset-semantic');
      const keywordBtn = screen.getByTestId('preset-keyword');

      expect(balancedBtn).toBeInTheDocument();
      expect(semanticBtn).toBeInTheDocument();
      expect(keywordBtn).toBeInTheDocument();

      // Trigger preset click
      fireEvent.click(semanticBtn);
      expect(setDense).toHaveBeenCalledWith(0.85);
      expect(setSparse).toHaveBeenCalledWith(0.15);
      expect(setTopK).toHaveBeenCalledWith(5);

      // Trigger top-k select change
      const topKSelect = screen.getByTestId('select-top-k');
      fireEvent.change(topKSelect, { target: { value: '8' } });
      expect(setTopK).toHaveBeenCalledWith(8);

      // Trigger reset
      const resetBtn = screen.getByTestId('btn-reset-filters');
      fireEvent.click(resetBtn);
      expect(setDense).toHaveBeenCalledWith(0.65);
      expect(setSparse).toHaveBeenCalledWith(0.35);
    });
  });

  describe('CitationDrawer Component', () => {
    const mockCitation: RAGCitationDetail = {
      citation_id: 'cite-1',
      chunk_id: 'chunk-1234',
      document_id: 'doc-5678',
      document_title: 'Global Compliance Manual.pdf',
      chunk_index: 4,
      page_number: 22,
      section: 'Section 3.1 Data Sovereignty',
      full_content: 'All user transaction records must reside within national borders.',
    };

    it('renders provenance details and handles close action', () => {
      const handleClose = vi.fn();

      render(
        <CitationDrawer
          citation={mockCitation}
          isOpen={true}
          onClose={handleClose}
          isLoading={false}
        />
      );

      expect(screen.getByTestId('citation-doc-title')).toHaveTextContent('Global Compliance Manual.pdf');
      expect(screen.getByText('Page 22')).toBeInTheDocument();
      expect(screen.getByText('Section 3.1 Data Sovereignty')).toBeInTheDocument();
      expect(screen.getByTestId('citation-full-content')).toHaveTextContent(
        'All user transaction records must reside within national borders.'
      );

      // Click close button
      const closeBtn = screen.getByTestId('btn-close-citation');
      fireEvent.click(closeBtn);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('does not render when isOpen is false', () => {
      render(
        <CitationDrawer
          citation={mockCitation}
          isOpen={false}
          onClose={vi.fn()}
        />
      );

      expect(screen.queryByTestId('citation-drawer')).toBeNull();
    });
  });

  describe('SessionHistorySidebar Component', () => {
    const mockSessions: RAGChatSessionItem[] = [
      {
        session_id: 'sess-1',
        title: 'Leave Policy Inquiries',
        created_at: '2026-10-25T08:00:00Z',
        updated_at: '2026-10-25T08:30:00Z',
        message_count: 4,
        messages: [],
      },
      {
        session_id: 'sess-2',
        title: 'Kubernetes Cluster Sizing',
        created_at: '2026-10-25T09:00:00Z',
        updated_at: '2026-10-25T09:15:00Z',
        message_count: 2,
        messages: [],
      },
    ];

    it('renders sessions list, triggers session switch and new session', () => {
      const handleSelect = vi.fn();
      const handleNew = vi.fn();

      render(
        <SessionHistorySidebar
          sessions={mockSessions}
          activeSessionId="sess-1"
          onSelectSession={handleSelect}
          onNewSession={handleNew}
          isOpen={true}
        />
      );

      expect(screen.getByText('Leave Policy Inquiries')).toBeInTheDocument();
      expect(screen.getByText('Kubernetes Cluster Sizing')).toBeInTheDocument();

      // Click second session
      const item2 = screen.getByTestId('session-item-sess-2');
      fireEvent.click(item2);
      expect(handleSelect).toHaveBeenCalledWith(mockSessions[1]);

      // Click new conversation
      const newBtn = screen.getByTestId('btn-new-conversation');
      fireEvent.click(newBtn);
      expect(handleNew).toHaveBeenCalledTimes(1);
    });

    it('filters sessions by search term', () => {
      render(
        <SessionHistorySidebar
          sessions={mockSessions}
          activeSessionId="sess-1"
          onSelectSession={vi.fn()}
          onNewSession={vi.fn()}
          isOpen={true}
        />
      );

      const searchInput = screen.getByTestId('input-search-sessions');
      fireEvent.change(searchInput, { target: { value: 'Kubernetes' } });

      expect(screen.queryByText('Leave Policy Inquiries')).toBeNull();
      expect(screen.getByText('Kubernetes Cluster Sizing')).toBeInTheDocument();
    });
  });

  describe('ChatThread Component', () => {
    it('renders empty starter prompts when no messages, and submits query on prompt click', () => {
      const handleSubmit = vi.fn();

      render(
        <ChatThread
          messages={[]}
          lastResponse={null}
          isLoading={false}
          error={null}
          onSubmitQuery={handleSubmit}
          onSelectCitation={vi.fn()}
          onSubmitFeedback={vi.fn().mockResolvedValue(true)}
        />
      );

      expect(screen.getByText('Enterprise Knowledge Q&A')).toBeInTheDocument();

      const starter = screen.getByTestId('prompt-starter-0');
      fireEvent.click(starter);
      expect(handleSubmit).toHaveBeenCalledWith('What is our enterprise employee leave policy?');
    });

    it('renders user and assistant messages with citations and triggers citation inspection', () => {
      const handleSelectCitation = vi.fn();
      const handleFeedback = vi.fn().mockResolvedValue(true);

      const mockMessages: RAGChatMessageItem[] = [
        {
          message_id: 'msg-u1',
          role: 'user',
          content: 'What is our travel policy?',
          created_at: '2026-10-25T10:00:00Z',
        },
        {
          message_id: 'msg-a1',
          role: 'assistant',
          content: 'Travel expenses must be submitted within 14 days [Source 1].',
          citations_json: JSON.stringify([
            {
              citation_id: 'cite-travel-1',
              document_id: 'doc-travel-1',
              document_title: 'Travel Policy 2026.pdf',
              page_number: 5,
              section: 'Expense Filing',
              chunk_id: 'chunk-t-1',
              similarity_score: 0.95,
              excerpt: 'All reimbursement claims must be submitted within 14 days...',
            },
          ]),
          created_at: '2026-10-25T10:00:02Z',
        },
      ];

      const mockResponse: RAGQueryResponse = {
        query_id: 'q-travel-1',
        query: 'What is our travel policy?',
        answer: 'Travel expenses must be submitted within 14 days [Source 1].',
        confidence_score: 0.95,
        is_grounded: true,
        processing_time_ms: 220,
        citations: [
          {
            citation_id: 'cite-travel-1',
            document_id: 'doc-travel-1',
            document_title: 'Travel Policy 2026.pdf',
            page_number: 5,
            section: 'Expense Filing',
            chunk_id: 'chunk-t-1',
            similarity_score: 0.95,
            excerpt: 'All reimbursement claims must be submitted within 14 days...',
          },
        ],
        retrieval_metrics: {
          dense_candidates: 10,
          sparse_candidates: 10,
          reranked_candidates: 5,
          latency_retrieval_ms: 100,
          latency_generation_ms: 120,
          tokens_prompt: 300,
          tokens_completion: 40,
        },
      };

      render(
        <ChatThread
          messages={mockMessages}
          lastResponse={mockResponse}
          isLoading={false}
          error={null}
          onSubmitQuery={vi.fn()}
          onSelectCitation={handleSelectCitation}
          onSubmitFeedback={handleFeedback}
        />
      );

      expect(screen.getByText('What is our travel policy?')).toBeInTheDocument();
      expect(screen.getByText('Travel expenses must be submitted within 14 days [Source 1].')).toBeInTheDocument();
      expect(screen.getByText('Grounded Response')).toBeInTheDocument();

      // Click citation chip
      const chip = screen.getByTestId('citation-chip-0');
      fireEvent.click(chip);
      expect(handleSelectCitation).toHaveBeenCalledWith(mockResponse.citations[0]);

      // Click positive feedback
      const thumbsUp = screen.getByTestId('btn-feedback-positive');
      fireEvent.click(thumbsUp);
      expect(handleFeedback).toHaveBeenCalledWith('q-travel-1', true);
    });
  });

  describe('RAGChatPage Master Integration', () => {
    it('mounts full page, loads initial history and statistics, and supports toggling', async () => {
      vi.mocked(ragService.getHistory).mockResolvedValueOnce({
        success: true,
        message: 'History retrieved successfully',
        data: {
          sessions: [],
          total: 0,
          page: 1,
          page_size: 20,
        },
      });

      vi.mocked(ragService.getStatistics).mockResolvedValueOnce({
        success: true,
        message: 'Statistics retrieved successfully',
        data: {
          organization_id: 'org-test',
          total_queries: 100,
          total_sessions: 20,
          average_latency_ms: 250,
          average_confidence_score: 0.91,
          hallucination_refusal_count: 2,
          positive_feedback_percentage: 95.0,
          total_citations_rendered: 300,
          cache_hit_ratio: 0.4,
        },
      });

      render(
        <MemoryRouter>
          <RAGChatPage />
        </MemoryRouter>
      );

      expect(screen.getByText('AI Knowledge Search & Q&A')).toBeInTheDocument();
      expect(screen.getByTestId('rag-chat-thread')).toBeInTheDocument();

      // Toggle executive telemetry
      const toggleMetricsBtn = screen.getByTestId('btn-toggle-metrics');
      fireEvent.click(toggleMetricsBtn);

      await waitFor(() => {
        expect(screen.getByTestId('rag-metrics-banner')).toBeInTheDocument();
      });

      // Toggle sidebar
      const toggleSidebarBtn = screen.getByTestId('btn-toggle-sidebar');
      fireEvent.click(toggleSidebarBtn);

      expect(screen.queryByTestId('rag-session-sidebar')).toBeNull();
    });
  });
});
