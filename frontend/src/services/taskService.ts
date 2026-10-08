/**
 * KEEP Enterprise Platform — Task API Client Service.
 * Connects frontend UI components to backend task persistence endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskFilterParams,
} from '@/types/task';

export const taskService = {
  /**
   * List tasks for projects or assignees.
   */
  async listTasks(
    params?: TaskFilterParams
  ): Promise<ApiResponse<PaginatedData<Task>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<Task>>>(
      '/tasks',
      { params }
    );
    return response.data;
  },

  /**
   * Get details for a specific task.
   */
  async getTask(id: string): Promise<ApiResponse<Task>> {
    const response = await apiClient.get<ApiResponse<Task>>(`/tasks/${id}`);
    return response.data;
  },

  /**
   * Create a new task.
   */
  async createTask(data: TaskCreate): Promise<ApiResponse<Task>> {
    const response = await apiClient.post<ApiResponse<Task>>('/tasks', data);
    return response.data;
  },

  /**
   * Update task status, priority, or assignee.
   */
  async updateTask(id: string, data: TaskUpdate): Promise<ApiResponse<Task>> {
    const response = await apiClient.patch<ApiResponse<Task>>(`/tasks/${id}`, data);
    return response.data;
  },

  /**
   * Soft delete a task.
   */
  async deleteTask(id: string): Promise<ApiResponse<{ id: string }>> {
    const response = await apiClient.delete<ApiResponse<{ id: string }>>(
      `/tasks/${id}`
    );
    return response.data;
  },
};
