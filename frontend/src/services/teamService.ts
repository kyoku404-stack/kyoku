/**
 * KEEP Enterprise Platform — Team API Client Service.
 * Connects frontend UI components to backend team persistence endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type { Team, TeamCreate, TeamUpdate } from '@/types/team';

export const teamService = {
  /**
   * List enterprise teams in tenant with optional filtering by department.
   */
  async listTeams(params?: {
    department_id?: string;
    skip?: number;
    limit?: number;
  }): Promise<ApiResponse<any>> {
    const config = params ? { params } : undefined;
    const response = await (config
      ? apiClient.get<ApiResponse<any>>('/teams', config)
      : apiClient.get<ApiResponse<any>>('/teams'));
    return response.data;
  },

  /**
   * Get specific team profile.
   */
  async getTeam(id: string): Promise<ApiResponse<Team>> {
    const response = await apiClient.get<ApiResponse<Team>>(`/teams/${id}`);
    return response.data;
  },

  /**
   * Create team.
   */
  async createTeam(data: TeamCreate): Promise<ApiResponse<Team>> {
    const response = await apiClient.post<ApiResponse<Team>>('/teams', data);
    return response.data;
  },

  /**
   * Update team.
   */
  async updateTeam(id: string, data: TeamUpdate): Promise<ApiResponse<Team>> {
    const response = await apiClient.patch<ApiResponse<Team>>(`/teams/${id}`, data);
    return response.data;
  },

  /**
   * Delete team.
   */
  async deleteTeam(id: string): Promise<ApiResponse<{ success: boolean }>> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(
      `/teams/${id}`
    );
    return response.data;
  },
};

export default teamService;
