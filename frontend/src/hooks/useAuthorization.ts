/**
 * KEEP Enterprise Platform — useAuthorization Custom Hook.
 * Implements fine-grained client-side RBAC evaluation, ownership override verification,
 * and tenant boundary gating aligned with Phase 1.6 architecture.
 */

import { useMemo } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import type { UserRole } from '@/types/auth';
import {
  OWNERSHIP_OVERRIDE_PERMISSIONS,
  ROLE_PERMISSIONS_MAP,
  type AuthDecision,
  type ResourceContext,
} from '@/types/permission';

export interface UseAuthorizationReturn {
  user: ReturnType<typeof useAuthStore.getState>['user'];
  role: UserRole;
  isSimulating: boolean;
  permissions: Set<string>;
  can: (permission: string, resource?: ResourceContext) => boolean;
  canAll: (permissions: string[]) => boolean;
  canAny: (permissions: string[]) => boolean;
  isRole: (role: UserRole | UserRole[]) => boolean;
  isAtLeast: (minRole: UserRole) => boolean;
  isOwner: (ownerId?: string) => boolean;
  evaluateAccess: (requiredPermission: string, resource?: ResourceContext) => AuthDecision;
  setSimulatedRole: (role: UserRole | null) => void;
}

export function useAuthorization(): UseAuthorizationReturn {
  const user = useAuthStore((state) => state.user);
  const simulatedRole = useAuthStore((state) => state.simulatedRole);
  const getEffectiveRole = useAuthStore((state) => state.getEffectiveRole);
  const isAtLeastRole = useAuthStore((state) => state.isAtLeastRole);
  const setSimulatedRole = useAuthStore((state) => state.setSimulatedRole);

  const role = getEffectiveRole();
  const permissions = useMemo(() => ROLE_PERMISSIONS_MAP[role] ?? new Set<string>(), [role]);
  const isSimulating = simulatedRole !== null;

  const isOwner = useMemo(() => {
    return (ownerId?: string) => {
      if (!user || !ownerId) return false;
      return user.id === ownerId;
    };
  }, [user]);

  const can = useMemo(() => {
    return (permission: string, resource?: ResourceContext): boolean => {
      // 1. Check direct role permission
      if (permissions.has(permission)) {
        return true;
      }

      // 2. Resource ownership override check
      if (resource?.ownerId && user && resource.ownerId === user.id) {
        if (OWNERSHIP_OVERRIDE_PERMISSIONS.has(permission)) {
          return true;
        }
      }

      return false;
    };
  }, [permissions, user]);

  const canAll = useMemo(() => {
    return (perms: string[]): boolean => {
      return perms.every((p) => permissions.has(p));
    };
  }, [permissions]);

  const canAny = useMemo(() => {
    return (perms: string[]): boolean => {
      return perms.some((p) => permissions.has(p));
    };
  }, [permissions]);

  const isRole = useMemo(() => {
    return (targetRole: UserRole | UserRole[]): boolean => {
      if (Array.isArray(targetRole)) {
        return targetRole.includes(role);
      }
      return role === targetRole;
    };
  }, [role]);

  const evaluateAccess = useMemo(() => {
    return (requiredPermission: string, resource?: ResourceContext): AuthDecision => {
      // Check tenant isolation if resource organizationId is specified
      if (resource?.organizationId && user?.organization_id) {
        if (resource.organizationId !== user.organization_id) {
          return {
            allowed: false,
            reason: 'Cross-tenant access is strictly prohibited',
            errorCode: 'AUTH_ORGANIZATION_MISMATCH',
            requiredPermission,
          };
        }
      }

      if (can(requiredPermission, resource)) {
        return {
          allowed: true,
          reason: `Granted permission '${requiredPermission}' for role ${role}`,
        };
      }

      return {
        allowed: false,
        reason: `Role '${role}' lacks required permission '${requiredPermission}'`,
        errorCode: 'AUTH_PERMISSION_DENIED',
        requiredPermission,
      };
    };
  }, [can, role, user]);

  return {
    user,
    role,
    isSimulating,
    permissions,
    can,
    canAll,
    canAny,
    isRole,
    isAtLeast: isAtLeastRole,
    isOwner,
    evaluateAccess,
    setSimulatedRole,
  };
}
