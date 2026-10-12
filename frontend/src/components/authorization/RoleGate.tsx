import React from 'react';
import { useAuthorization } from '@/hooks/useAuthorization';
import type { UserRole } from '@/types/auth';

export interface RoleGateProps {
  /** Explicit list of roles allowed to view the children */
  allowedRoles?: UserRole[];
  /** Minimum hierarchy level role required */
  minRole?: UserRole;
  /** Fallback content rendered if role evaluation fails (defaults to null) */
  fallback?: React.ReactNode;
  /** Content rendered when access is granted */
  children: React.ReactNode;
}

/**
 * Declarative component gate that renders children only when the authenticated
 * user has an approved role or meets the minimum role hierarchy level.
 */
export const RoleGate: React.FC<RoleGateProps> = ({
  allowedRoles,
  minRole,
  fallback = null,
  children,
}) => {
  const { isRole, isAtLeast } = useAuthorization();

  if (allowedRoles && allowedRoles.length > 0 && !isRole(allowedRoles)) {
    return <>{fallback}</>;
  }

  if (minRole && !isAtLeast(minRole)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
