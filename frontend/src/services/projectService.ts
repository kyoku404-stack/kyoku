/**
 * KEEP Enterprise Platform — Project API Client Service.
 * Connects frontend UI components to backend project persistence endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectFilterParams,
} from '@/types/project';

export const projectService = {
  /**
   * List enterprise projects with optional pagination and filtering.
   */
  async listProjects(
    params?: ProjectFilterParams
  ): Promise<ApiResponse<PaginatedData<Project>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<Project>>>(
      '/projects',
      { params }
    );
    return response.data;
  },

  /**
   * Get details for a specific project.
   */
  async getProject(id: string): Promise<ApiResponse<Project>> {
    const response = await apiClient.get<ApiResponse<Project>>(`/projects/${id}`);
    return response.data;
  },

  /**
   * Create a new project workspace.
   */
  async createProject(data: ProjectCreate): Promise<ApiResponse<Project>> {
    const response = await apiClient.post<ApiResponse<Project>>('/projects', data);
    return response.data;
  },

  /**
   * Update project details.
   */
  async updateProject(
    id: string,
    data: ProjectUpdate
  ): Promise<ApiResponse<Project>> {
    const response = await apiClient.patch<ApiResponse<Project>>(
      `/projects/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Soft delete a project.
   */
  async deleteProject(id: string): Promise<ApiResponse<{ id: string }>> {
    const response = await apiClient.delete<ApiResponse<{ id: string }>>(
      `/projects/${id}`
    );
    return response.data;
  },
};
