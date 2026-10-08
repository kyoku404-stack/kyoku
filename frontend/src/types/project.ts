/**
 * KEEP Enterprise Platform — Project Domain Types.
 * Aligned with database schema `projects` table (docs/database/database-schema.md).
 */

export type ProjectStatus = 'ACTIVE' | 'ARCHIVED' | 'COMPLETED';
export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Project {
  id: string;
  organization_id: string;
  team_id?: string | null;
  owner_id: string;
  name: string;
  description?: string | null;
  status: ProjectStatus;
  priority: ProjectPriority;
  document_count?: number;
  meeting_count?: number;
  task_count?: number;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  team_id?: string;
  status?: ProjectStatus;
  priority?: ProjectPriority;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  team_id?: string;
  status?: ProjectStatus;
  priority?: ProjectPriority;
}

export interface ProjectFilterParams {
  page?: number;
  page_size?: number;
  status?: ProjectStatus;
  priority?: ProjectPriority;
  team_id?: string;
  search?: string;
}
