/**
 * KEEP Enterprise Platform — Team & Workspace Data Models.
 * Aligned with database schema `teams` & `team_members` tables.
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
  name: string;
  description?: string | null;
  lead_user_id?: string | null;
  members_count?: number;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface TeamCreate {
  name: string;
  description?: string;
  lead_user_id?: string;
}

export interface TeamUpdate {
  name?: string;
  description?: string;
  lead_user_id?: string;
}
