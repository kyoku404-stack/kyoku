/**
 * KEEP Enterprise Platform — Department API Client Service.
 * Connects frontend UI components to backend department management endpoints (/api/v1/departments).
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  DepartmentResponse,
  DepartmentCreate,
  DepartmentUpdate,
} from '@/types/department';

export const departmentService = {
  /**
   * List enterprise departments with optional pagination.
   * GET /api/v1/departments
   */
  async listDepartments(
    skip = 0,
    limit = 100
  ): Promise<ApiResponse<DepartmentResponse[]>> {
    const response = await apiClient.get<ApiResponse<DepartmentResponse[]>>(
      '/departments',
      { params: { skip, limit } }
    );
    return response.data;
  },

  /**
   * Retrieve a specific department by ID.
   * GET /api/v1/departments/{id}
   */
  async getDepartment(id: string): Promise<ApiResponse<DepartmentResponse>> {
    const response = await apiClient.get<ApiResponse<DepartmentResponse>>(
      `/departments/${id}`
    );
    return response.data;
  },

  /**
   * Create a new organizational department.
   * POST /api/v1/departments
   */
  async createDepartment(
    data: DepartmentCreate
  ): Promise<ApiResponse<DepartmentResponse>> {
    const response = await apiClient.post<ApiResponse<DepartmentResponse>>(
      '/departments',
      data
    );
    return response.data;
  },

  /**
   * Update department name, description, or manager.
   * PATCH /api/v1/departments/{id}
   */
  async updateDepartment(
    id: string,
    data: DepartmentUpdate
  ): Promise<ApiResponse<DepartmentResponse>> {
    const response = await apiClient.patch<ApiResponse<DepartmentResponse>>(
      `/departments/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Delete a department from the tenant organization.
   * DELETE /api/v1/departments/{id}
   */
  async deleteDepartment(id: string): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(
      `/departments/${id}`
    );
    return response.data;
  },
};

export default departmentService;
