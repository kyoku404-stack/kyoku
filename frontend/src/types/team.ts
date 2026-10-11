/**
 * KEEP Enterprise Platform — Team & Workspace Data Models.
 * Aligned with database schema `teams` & `team_members` tables and backend team schemas.
 */

export type TeamRole = 'Lead' | 'Member' | 'Observer';

export interface TeamMember {
  team_id: string;
  user_id: string;
  role_in_team: TeamRole;
  user_full_name?: string;
  user_email?: string;
  created_at: string;
}

export interface Team {
  id: string;
  organization_id: string;
  department_id?: string | null;
  name: string;
  description?: string | null;
  lead_user_id?: string | null;
  members_count?: number;
  member_count?: number;
  is_deleted?: boolean;
  created_at: string;
  updated_at?: string | null;
}

export type TeamResponse = Team;

export interface TeamCreate {
  name: string;
  department_id?: string | null;
  lead_user_id?: string | null;
  description?: string | null;
}

export interface TeamUpdate {
  name?: string | null;
  department_id?: string | null;
  lead_user_id?: string | null;
  description?: string | null;
}
