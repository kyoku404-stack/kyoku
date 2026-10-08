/**
 * KEEP Enterprise Platform — Meeting API Client Service.
 * Connects frontend UI components to backend meeting persistence endpoints.
 */

import { apiClient } from './api';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  Meeting,
  MeetingCreate,
  MeetingUpdate,
  MeetingFilterParams,
} from '@/types/meeting';

export const meetingService = {
  /**
   * List scheduled or recorded meetings.
   */
  async listMeetings(
    params?: MeetingFilterParams
  ): Promise<ApiResponse<PaginatedData<Meeting>>> {
    const response = await apiClient.get<ApiResponse<PaginatedData<Meeting>>>(
      '/meetings',
      { params }
    );
    return response.data;
  },

  /**
   * Get specific meeting record.
   */
  async getMeeting(id: string): Promise<ApiResponse<Meeting>> {
    const response = await apiClient.get<ApiResponse<Meeting>>(`/meetings/${id}`);
    return response.data;
  },

  /**
   * Schedule or log a new meeting.
   */
  async createMeeting(data: MeetingCreate): Promise<ApiResponse<Meeting>> {
    const response = await apiClient.post<ApiResponse<Meeting>>('/meetings', data);
    return response.data;
  },

  /**
   * Update meeting details (transcripts, summary, recording link).
   */
  async updateMeeting(
    id: string,
    data: MeetingUpdate
  ): Promise<ApiResponse<Meeting>> {
    const response = await apiClient.patch<ApiResponse<Meeting>>(
      `/meetings/${id}`,
      data
    );
    return response.data;
  },
};
