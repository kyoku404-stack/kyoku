/**
 * Phase 2.3 Enterprise AI Assistant & Agentic Workflows API Client Service.
 * Implements communication with all 7 Phase 2.3 REST endpoints:
 * - POST /api/v1/assistant/chat
 * - POST /api/v1/assistant/task
 * - GET  /api/v1/assistant/history
 * - POST /api/v1/assistant/report
 * - GET  /api/v1/assistant/workflows
 * - POST /api/v1/assistant/approve
 * - GET  /api/v1/assistant/recommendations
 *
 * Specification: docs/api/api-contract.md Section 10 & devdocs/p2/p2.3.txt Chapter 16
 * Author: Member 3 (Frontend Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  AssistantChatRequest,
  AssistantChatResponseData,
  TaskExecuteRequest,
  TaskExecuteResponseData,
  ReportGenerateRequest,
  ReportGenerateResponseData,
  WorkflowListResponseData,
  ApprovalActionRequest,
  ApprovalActionResponseData,
  RecommendationResponseData,
} from '@/types/assistant';

export interface AssistantHistoryResponse {
  sessions: Array<{
    session_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    messages: Array<{
      id: string;
      role: 'user' | 'assistant';
      content: string;
      created_at: string;
    }>;
  }>;
  total: number;
  page: number;
  page_size: number;
}

export const assistantService = {
  /**
   * Send a conversational message to the AI Assistant.
   * POST /api/v1/assistant/chat
   */
  async chat(payload: AssistantChatRequest): Promise<ApiResponse<AssistantChatResponseData>> {
    const response = await apiClient.post<ApiResponse<AssistantChatResponseData>>(
      '/assistant/chat',
      payload
    );
    return response.data;
  },

  /**
   * Execute an automated multi-step DAG task workflow.
   * POST /api/v1/assistant/task
   */
  async executeTask(payload: TaskExecuteRequest): Promise<ApiResponse<TaskExecuteResponseData>> {
    const response = await apiClient.post<ApiResponse<TaskExecuteResponseData>>(
      '/assistant/task',
      payload
    );
    return response.data;
  },

  /**
   * Retrieve conversational history sessions.
   * GET /api/v1/assistant/history
   */
  async getHistory(
    sessionId?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<AssistantHistoryResponse>> {
    const response = await apiClient.get<ApiResponse<AssistantHistoryResponse>>(
      '/assistant/history',
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
   * Generate a structured organizational report.
   * POST /api/v1/assistant/report
   */
  async generateReport(
    payload: ReportGenerateRequest
  ): Promise<ApiResponse<ReportGenerateResponseData>> {
    const response = await apiClient.post<ApiResponse<ReportGenerateResponseData>>(
      '/assistant/report',
      payload
    );
    return response.data;
  },

  /**
   * Query workflows and DAG execution progress.
   * GET /api/v1/assistant/workflows
   */
  async getWorkflows(
    status?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<WorkflowListResponseData>> {
    const response = await apiClient.get<ApiResponse<WorkflowListResponseData>>(
      '/assistant/workflows',
      {
        params: {
          status,
          page,
          page_size: pageSize,
        },
      }
    );
    return response.data;
  },

  /**
   * Submit human-in-the-loop approval or rejection for a sensitive action.
   * POST /api/v1/assistant/approve
   */
  async processApproval(
    payload: ApprovalActionRequest
  ): Promise<ApiResponse<ApprovalActionResponseData>> {
    const response = await apiClient.post<ApiResponse<ApprovalActionResponseData>>(
      '/assistant/approve',
      payload
    );
    return response.data;
  },

  /**
   * Retrieve proactive enterprise recommendations and insights.
   * GET /api/v1/assistant/recommendations
   */
  async getRecommendations(): Promise<ApiResponse<RecommendationResponseData>> {
    const response = await apiClient.get<ApiResponse<RecommendationResponseData>>(
      '/assistant/recommendations'
    );
    return response.data;
  },
};
