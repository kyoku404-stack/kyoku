/**
 * KEEP Enterprise Platform — Phase 4.2 Agent Runtime & Execution Engine API Client Service.
 *
 * Consumes KEEP's Phase 4.1 Discovery (`/agents`) and Phase 4.2 Execution Runtime
 * (`/agents/{agent_id}/executions`, `/executions`, `/executions/metrics`,
 * `/executions/{id}`, `/executions/{id}/result`, `/cancel`, `/retry`) REST endpoints.
 */

import { apiClient } from './api';
import type {
  AgentListResponse,
  ExecutionListResponse,
  ExecutionResultResponse,
  ExecutionSingleResponse,
  ExecutionStatus,
  RetryExecutionRequest,
  RuntimeMetricsResponse,
  SubmitExecutionRequest,
} from '@/types/agentRuntime';

export const agentRuntimeService = {
  /**
   * Lists registered agents visible to the authenticated user.
   */
  async listAgents(params?: {
    capability?: string;
    include_disabled?: boolean;
  }): Promise<AgentListResponse> {
    const response = await apiClient.get<AgentListResponse>('/agents', { params });
    return response.data;
  },

  /**
   * Submits a synchronous or asynchronous execution for the specified agent.
   */
  async submitExecution(
    agentId: string,
    payload: SubmitExecutionRequest,
    idempotencyKey?: string
  ): Promise<ExecutionSingleResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey && idempotencyKey.trim()) {
      headers['Idempotency-Key'] = idempotencyKey.trim();
    }
    const response = await apiClient.post<ExecutionSingleResponse>(
      `/agents/${encodeURIComponent(agentId)}/executions`,
      payload,
      Object.keys(headers).length > 0 ? { headers } : undefined
    );
    return response.data;
  },

  /**
   * Lists tenant-scoped agent executions with optional agent/status filtering.
   */
  async listExecutions(params?: {
    agent_id?: string;
    status?: ExecutionStatus;
    limit?: number;
  }): Promise<ExecutionListResponse> {
    const response = await apiClient.get<ExecutionListResponse>('/executions', { params });
    return response.data;
  },

  /**
   * Retrieves lifecycle metadata and status for a single execution.
   */
  async getExecution(executionId: string): Promise<ExecutionSingleResponse> {
    const response = await apiClient.get<ExecutionSingleResponse>(
      `/executions/${encodeURIComponent(executionId)}`
    );
    return response.data;
  },

  /**
   * Retrieves the validated structured output, evidence citations, and warnings for a completed execution.
   */
  async getExecutionResult(executionId: string): Promise<ExecutionResultResponse> {
    const response = await apiClient.get<ExecutionResultResponse>(
      `/executions/${encodeURIComponent(executionId)}/result`
    );
    return response.data;
  },

  /**
   * Requests atomic or cooperative cancellation for a pending, queued, or running execution.
   */
  async cancelExecution(executionId: string): Promise<ExecutionSingleResponse> {
    const response = await apiClient.post<ExecutionSingleResponse>(
      `/executions/${encodeURIComponent(executionId)}/cancel`
    );
    return response.data;
  },

  /**
   * Creates a linked retry execution attempt for an eligible failed or timed-out execution.
   */
  async retryExecution(
    executionId: string,
    payload?: RetryExecutionRequest
  ): Promise<ExecutionSingleResponse> {
    const response = await apiClient.post<ExecutionSingleResponse>(
      `/executions/${encodeURIComponent(executionId)}/retry`,
      payload ?? {}
    );
    return response.data;
  },

  /**
   * Retrieves runtime observability KPIs and recent secret-safe lifecycle events.
   */
  async getMetrics(): Promise<RuntimeMetricsResponse> {
    const response = await apiClient.get<RuntimeMetricsResponse>('/executions/metrics');
    return response.data;
  },
};
