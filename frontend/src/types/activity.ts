/**
 * KEEP Enterprise Platform — Activity Log / Audit Trail Types.
 * Aligned with database schema `activity_logs` table.
 */

export interface ActivityLog {
  id: string;
  organization_id: string;
  user_id?: string | null;
  user_full_name?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface ActivityLogFilterParams {
  page?: number;
  page_size?: number;
  user_id?: string;
  action?: string;
  resource_type?: string;
  search?: string;
}
