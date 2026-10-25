/**
 * KEEP Enterprise Platform — RAG Service Unit Tests (Phase 2.2).
 *
 * Verifies that all 5 REST API service endpoints in ragService conform to:
 * - POST /api/v1/rag/query
 * - GET  /api/v1/rag/history
 * - GET  /api/v1/rag/citations/{id}
 * - POST /api/v1/rag/feedback
 * - GET  /api/v1/rag/statistics
 *
 * Specification: devdocs/p2/p2.2.txt Chapter 16 & docs/api/api-contract.md Section 9
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ragService } from '@/services/ragService';
import { apiClient } from '@/services/api';
import type {
  RAGQueryRequest,
  RAGQueryResponse,
  RAGHistoryResponse,
  RAGCitationDetail,
  RAGFeedbackRequest,
  RAGFeedbackResponse,
  RAGStatistics,
} from '@/types/rag';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 2.2 RAG Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('queryRAG() posts natural language question and returns RAGQueryResponse', async () => {
    const mockRequest: RAGQueryRequest = {
      query: 'What is our enterprise leave policy?',
      hybrid_dense_weight: 0.65,
      hybrid_sparse_weight: 0.35,
      top_k: 5,
    };

    const mockResponse: { data: { success: boolean; message: string; data: RAGQueryResponse } } = {
      data: {
        success: true,
        message: 'RAG query answered successfully.',
        data: {
          query_id: 'q-uuid-1234',
          session_id: 'sess-uuid-5678',
          query: 'What is our enterprise leave policy?',
          answer: 'Employees are entitled to 20 days paid leave [Source 1].',
          confidence_score: 0.92,
          is_grounded: true,
          processing_time_ms: 280,
          citations: [
            {
              citation_id: 'cite-uuid-1',
              document_id: 'doc-uuid-1',
              document_title: 'Employee Handbook.pdf',
              page_number: 18,
              section: 'Section 4.2 Leave Policy',
              chunk_id: 'chunk-uuid-1',
              similarity_score: 0.94,
              excerpt: 'Employees are entitled to 20 days of paid annual leave...',
            },
          ],
          retrieval_metrics: {
            dense_candidates: 10,
            sparse_candidates: 10,
            reranked_candidates: 5,
            latency_retrieval_ms: 120,
            latency_generation_ms: 160,
            tokens_prompt: 450,
            tokens_completion: 65,
          },
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

    const result = await ragService.queryRAG(mockRequest);

    expect(apiClient.post).toHaveBeenCalledWith('/rag/query', mockRequest);
    expect(result.success).toBe(true);
    expect(result.data.query_id).toBe('q-uuid-1234');
    expect(result.data.citations.length).toBe(1);
    expect(result.data.is_grounded).toBe(true);
  });

  it('getHistory() retrieves conversational sessions and message threads', async () => {
    const mockResponse: { data: { success: boolean; data: RAGHistoryResponse } } = {
      data: {
        success: true,
        data: {
          sessions: [
            {
              session_id: 'sess-123',
              title: 'Leave Policy Query',
              created_at: '2026-10-25T10:00:00Z',
              updated_at: '2026-10-25T10:05:00Z',
              message_count: 2,
              messages: [
                {
                  message_id: 'msg-1',
                  role: 'user',
                  content: 'Summarize the leave policy',
                  created_at: '2026-10-25T10:00:00Z',
                },
              ],
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

    const result = await ragService.getHistory('sess-123', 1, 20);

    expect(apiClient.get).toHaveBeenCalledWith('/rag/history', {
      params: { session_id: 'sess-123', page: 1, page_size: 20 },
    });
    expect(result.success).toBe(true);
    expect(result.data.sessions.length).toBe(1);
    expect(result.data.sessions[0].session_id).toBe('sess-123');
  });

  it('getCitationDetail() retrieves deep chunk provenance content', async () => {
    const mockResponse: { data: { success: boolean; data: RAGCitationDetail } } = {
      data: {
        success: true,
        data: {
          citation_id: 'cite-123',
          chunk_id: 'chunk-456',
          document_id: 'doc-789',
          document_title: 'AWS Security Architecture.pdf',
          chunk_index: 3,
          page_number: 14,
          section: 'KMS Key Retention',
          full_content: 'All symmetric encryption keys must be rotated every 365 days...',
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

    const result = await ragService.getCitationDetail('chunk-456');

    expect(apiClient.get).toHaveBeenCalledWith('/rag/citations/chunk-456');
    expect(result.success).toBe(true);
    expect(result.data.page_number).toBe(14);
    expect(result.data.full_content).toContain('symmetric encryption keys');
  });

  it('submitFeedback() sends user rating and comment', async () => {
    const feedbackPayload: RAGFeedbackRequest = {
      query_id: 'q-123',
      rating: 5,
      is_helpful: true,
      comment: 'Very clear explanation with precise citation!',
    };

    const mockResponse: { data: { success: boolean; data: RAGFeedbackResponse } } = {
      data: {
        success: true,
        data: {
          feedback_id: 'fb-uuid-999',
          recorded_at: '2026-10-25T11:00:00Z',
        },
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

    const result = await ragService.submitFeedback(feedbackPayload);

    expect(apiClient.post).toHaveBeenCalledWith('/rag/feedback', feedbackPayload);
    expect(result.success).toBe(true);
    expect(result.data.feedback_id).toBe('fb-uuid-999');
  });

  it('getStatistics() retrieves aggregate RAG performance metrics', async () => {
    const mockResponse: { data: { success: boolean; data: RAGStatistics } } = {
      data: {
        success: true,
        data: {
          organization_id: 'org-123',
          total_queries: 1420,
          total_sessions: 310,
          average_latency_ms: 245.5,
          average_confidence_score: 0.892,
          hallucination_refusal_count: 8,
          positive_feedback_percentage: 94.6,
          total_citations_rendered: 4260,
          cache_hit_ratio: 0.42,
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

    const result = await ragService.getStatistics();

    expect(apiClient.get).toHaveBeenCalledWith('/rag/statistics');
    expect(result.success).toBe(true);
    expect(result.data.total_queries).toBe(1420);
    expect(result.data.average_latency_ms).toBe(245.5);
    expect(result.data.positive_feedback_percentage).toBe(94.6);
  });
});
