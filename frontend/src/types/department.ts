/**
 * KEEP Enterprise Platform — Department Domain Types.
 * Aligned with backend schemas (backend/app/schemas/department.py) and PostgreSQL `departments` table.
 */

export interface Department {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  manager_id?: string | null;
  team_count?: number;
  member_count?: number;
  created_at: string;
  updated_at?: string | null;
}

export type DepartmentResponse = Department;

export interface DepartmentCreate {
  name: string;
  description?: string | null;
  manager_id?: string | null;
}

export interface DepartmentUpdate {
  name?: string | null;
  description?: string | null;
  manager_id?: string | null;
}
