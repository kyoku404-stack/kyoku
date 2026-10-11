/**
 * KEEP Enterprise Platform — User Invitation Domain Types.
 * Aligned with backend schemas (backend/app/schemas/invitation.py) and PostgreSQL `invitations` table.
 */

export type InvitationStatus = 'PENDING' | 'ACCEPTED' | 'REVOKED' | 'EXPIRED';

export interface Invitation {
  id: string;
  organization_id: string;
  department_id?: string | null;
  team_id?: string | null;
  email: string;
  role: string;
  token: string;
  status: InvitationStatus | string;
  invited_by_id: string;
  expires_at: string;
  created_at: string;
  updated_at?: string | null;
}

export type InvitationResponse = Invitation;

export interface InvitationCreate {
  email: string;
  role?: string;
  department_id?: string | null;
  team_id?: string | null;
}

export interface InvitationAccept {
  token: string;
  full_name: string;
  password: string;
}
