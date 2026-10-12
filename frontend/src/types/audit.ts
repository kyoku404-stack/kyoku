/**
 * KEEP Enterprise Platform — Security Audit & Activity Log Types.
 * Aligned with backend schema (backend/app/schemas/audit.py).
 */

export interface AuditLogEntry {
  id: string;
  organization_id: string;
  user_id?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  details?: string | null;
  ip_address?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface AuditLogQueryParams {
  page?: number;
  page_size?: number;
  action?: string;
  resource_type?: string;
  user_id?: string;
}
