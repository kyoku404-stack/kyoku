/**
 * KEEP Enterprise Platform — Team API Client Service.
 * Connects frontend UI components to backend team persistence endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type { Team, TeamCreate, TeamUpdate } from '@/types/team';

export const teamService = {
  /**
   * List enterprise teams in tenant.
   */
  async listTeams(): Promise<ApiResponse<PaginatedData<Team>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<Team>>>('/teams');
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
   * Create team department.
   */
  async createTeam(data: TeamCreate): Promise<ApiResponse<Team>> {
    const response = await apiClient.post<ApiResponse<Team>>('/teams', data);
    return response.data;
  },

  /**
   * Update team department.
   */
  async updateTeam(id: string, data: TeamUpdate): Promise<ApiResponse<Team>> {
    const response = await apiClient.patch<ApiResponse<Team>>(`/teams/${id}`, data);
    return response.data;
  },
};
