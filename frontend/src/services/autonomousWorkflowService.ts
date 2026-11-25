/**
 * KEEP Enterprise Platform — Phase 4.9 Autonomous Workflow Engine API Service.
 *
 * Consumes KEEP's Phase 4.9 endpoints using relative paths over `apiClient`:
 * - `GET  /autonomous-workflows`
 * - `POST /autonomous-workflows`
 * - `GET  /autonomous-workflows/{id}`
 * - `GET  /autonomous-workflows/{id}/steps`
 * - `GET  /autonomous-workflows/{id}/events`
 * - `POST /autonomous-workflows/{id}/cancel`
 * - `POST /autonomous-workflows/{id}/resume`
 */

import { apiClient } from './api';
import type {
  AutonomousStepsResponse,
  AutonomousTimelineApiResponse,
  AutonomousWorkflowListResponse,
  AutonomousWorkflowRequest,
  AutonomousWorkflowResponse,
  AutonomyStatus,
  CancelWorkflowRequest,
  ResumeWorkflowRequest,
} from '@/types/autonomy';

export const autonomousWorkflowService = {
  async listWorkflows(params?: {
    status?: AutonomyStatus;
    limit?: number;
  }): Promise<AutonomousWorkflowListResponse> {
    const response = await apiClient.get<AutonomousWorkflowListResponse>('/autonomous-workflows', {
      params,
    });
    return response.data;
  },

  async startWorkflow(
    payload: AutonomousWorkflowRequest
  ): Promise<AutonomousWorkflowResponse> {
    const response = await apiClient.post<AutonomousWorkflowResponse>(
      '/autonomous-workflows',
      payload
    );
    return response.data;
  },

  async getWorkflow(executionId: string): Promise<AutonomousWorkflowResponse> {
    const response = await apiClient.get<AutonomousWorkflowResponse>(
      `/autonomous-workflows/${encodeURIComponent(executionId)}`
    );
    return response.data;
  },

  async listSteps(executionId: string): Promise<AutonomousStepsResponse> {
    const response = await apiClient.get<AutonomousStepsResponse>(
      `/autonomous-workflows/${encodeURIComponent(executionId)}/steps`
    );
    return response.data;
  },

  async getEvents(executionId: string): Promise<AutonomousTimelineApiResponse> {
    const response = await apiClient.get<AutonomousTimelineApiResponse>(
      `/autonomous-workflows/${encodeURIComponent(executionId)}/events`
    );
    return response.data;
  },

  async cancelWorkflow(
    executionId: string,
    payload: CancelWorkflowRequest = { reason: 'Cancelled by operator' }
  ): Promise<AutonomousWorkflowResponse> {
    const response = await apiClient.post<AutonomousWorkflowResponse>(
      `/autonomous-workflows/${encodeURIComponent(executionId)}/cancel`,
      payload
    );
    return response.data;
  },

  async resumeWorkflow(
    executionId: string,
    payload: ResumeWorkflowRequest = { approve: true, reason: 'Approved by authorized operator' }
  ): Promise<AutonomousWorkflowResponse> {
    const response = await apiClient.post<AutonomousWorkflowResponse>(
      `/autonomous-workflows/${encodeURIComponent(executionId)}/resume`,
      payload
    );
    return response.data;
  },
};
