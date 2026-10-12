import React from 'react';
import { useAuthorization } from '@/hooks/useAuthorization';
import type { ResourceContext } from '@/types/permission';

export interface PermissionGateProps {
  /** Single required action permission */
  permission?: string;
  /** Grant access if user possesses ANY of these permissions */
  anyOf?: string[];
  /** Grant access only if user possesses ALL of these permissions */
  allOf?: string[];
  /** Optional resource context for ownership override checks */
  resource?: ResourceContext;
  /** Fallback content rendered if permission evaluation fails (defaults to null) */
  fallback?: React.ReactNode;
  /** Content rendered when access is granted */
  children: React.ReactNode;
}

/**
 * Declarative component gate that renders children only when the authenticated
 * user possesses the required fine-grained permissions.
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
  permission,
  anyOf,
  allOf,
  resource,
  fallback = null,
  children,
}) => {
  const { can, canAny, canAll } = useAuthorization();

  // 1. Single permission check with optional ownership override
  if (permission && !can(permission, resource)) {
    return <>{fallback}</>;
  }

  // 2. AnyOf check
  if (anyOf && anyOf.length > 0 && !canAny(anyOf)) {
    return <>{fallback}</>;
  }

  // 3. AllOf check
  if (allOf && allOf.length > 0 && !canAll(allOf)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
