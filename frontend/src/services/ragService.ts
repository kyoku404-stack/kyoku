/**
 * Phase 2.2 RAG Engine & Semantic Search API Client Service.
 * Implements communication with all 5 Phase 2.2 REST endpoints:
 * - POST /api/v1/rag/query
 * - GET  /api/v1/rag/history
 * - GET  /api/v1/rag/citations/{id}
 * - POST /api/v1/rag/feedback
 * - GET  /api/v1/rag/statistics
 *
 * Specification: docs/api/api-contract.md Section 9 & devdocs/p2/p2.2.txt Chapter 16
 * Author: Member 3 (Frontend Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  RAGQueryRequest,
  RAGQueryResponse,
  RAGHistoryResponse,
  RAGCitationDetail,
  RAGFeedbackRequest,
  RAGFeedbackResponse,
  RAGStatistics,
} from '@/types/rag';

export const ragService = {
  /**
   * Submit natural language question for grounded RAG answer synthesis.
   * POST /api/v1/rag/query -> 200 OK
   */
  async queryRAG(payload: RAGQueryRequest): Promise<ApiResponse<RAGQueryResponse>> {
    const response = await apiClient.post<ApiResponse<RAGQueryResponse>>(
      '/rag/query',
      payload
    );
    return response.data;
  },

  /**
   * Retrieve conversational session history and exchange messages.
   * GET /api/v1/rag/history -> 200 OK
   */
  async getHistory(
    sessionId?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<RAGHistoryResponse>> {
    const response = await apiClient.get<ApiResponse<RAGHistoryResponse>>(
      '/rag/history',
      {
        params: {
          session_id: sessionId,
          page,
          page_size: pageSize,
        },
      }
    );
    return response.data;
  },

  /**
   * Retrieve deep source provenance and full content for a citation chunk.
   * GET /api/v1/rag/citations/{citation_id} -> 200 OK
   */
  async getCitationDetail(citationId: string): Promise<ApiResponse<RAGCitationDetail>> {
    const response = await apiClient.get<ApiResponse<RAGCitationDetail>>(
      `/rag/citations/${citationId}`
    );
    return response.data;
  },

  /**
   * Submit user satisfaction feedback (rating, comment) for a generated answer.
   * POST /api/v1/rag/feedback -> 200 OK
   */
  async submitFeedback(payload: RAGFeedbackRequest): Promise<ApiResponse<RAGFeedbackResponse>> {
    const response = await apiClient.post<ApiResponse<RAGFeedbackResponse>>(
      '/rag/feedback',
      payload
    );
    return response.data;
  },

  /**
   * Retrieve organizational RAG engine statistics and performance metrics.
   * GET /api/v1/rag/statistics -> 200 OK
   */
  async getStatistics(): Promise<ApiResponse<RAGStatistics>> {
    const response = await apiClient.get<ApiResponse<RAGStatistics>>(
      '/rag/statistics'
    );
    return response.data;
  },
};
