/**
 * KEEP Enterprise Platform — Meeting Domain Types.
 * Aligned with database schema `meetings` table.
 */

export interface Meeting {
  id: string;
  organization_id: string;
  project_id?: string | null;
  organizer_id: string;
  title: string;
  scheduled_start: string;
  scheduled_end: string;
  recording_url?: string | null;
  transcript_text?: string | null;
  summary_text?: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface MeetingCreate {
  title: string;
  scheduled_start: string;
  scheduled_end: string;
  project_id?: string;
  recording_url?: string;
  transcript_text?: string;
  summary_text?: string;
}

export interface MeetingUpdate {
  title?: string;
  scheduled_start?: string;
  scheduled_end?: string;
  recording_url?: string;
  transcript_text?: string;
  summary_text?: string;
}

export interface MeetingFilterParams {
  page?: number;
  page_size?: number;
  project_id?: string;
  search?: string;
}
