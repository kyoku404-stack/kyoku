/**
 * KEEP Enterprise Platform — Task Domain Types.
 * Aligned with database schema `tasks` table.
 */

export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Task {
  id: string;
  organization_id: string;
  project_id?: string | null;
  creator_id: string;
  assignee_id?: string | null;
  title: string;
  description?: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_date?: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface TaskCreate {
  title: string;
  description?: string;
  project_id?: string;
  assignee_id?: string;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  assignee_id?: string;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string;
}

export interface TaskFilterParams {
  page?: number;
  page_size?: number;
  project_id?: string;
  assignee_id?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
}
