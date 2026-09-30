/**
 * KEEP Enterprise Platform — Authentication & Identity Types.
 * Aligned with backend schemas (backend/app/schemas/auth.py & user.py).
 */

export type UserRole = 'SuperAdmin' | 'OrgAdmin' | 'Manager' | 'Member' | 'Viewer' | 'Guest';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserSummaryResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
  expires_in: number;
  user: UserSummaryResponse;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

/**
 * Backward compatibility type for User representing user profile.
 */
export interface User extends UserProfileResponse {}

/**
 * Backward compatibility type for organization entity.
 */
export interface Organization {
  id: string;
  name: string;
  domain?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

/**
 * Backward compatibility type for LoginResponse.
 */
export interface LoginResponse extends Partial<TokenResponse> {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user?: User;
}
