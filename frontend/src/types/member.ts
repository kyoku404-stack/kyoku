/**
 * KEEP Enterprise Platform — Organization Member Management Types.
 * Aligned with backend schemas (backend/app/schemas/member.py).
 */

export interface MemberResponse {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: string;
  department_id?: string | null;
  team_id?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface MemberUpdate {
  role?: string | null;
  department_id?: string | null;
  team_id?: string | null;
  is_active?: boolean | null;
}

export interface MemberListQuery {
  department_id?: string;
  team_id?: string;
  role?: string;
  page?: number;
  page_size?: number;
  search?: string;
}
