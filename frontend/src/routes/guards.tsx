import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import { useAuthorization } from '@/hooks/useAuthorization';
import { ROUTES } from './paths';
import type { UserRole } from '@/types/auth';

interface RequireAuthProps {
  children: React.ReactNode;
}

/**
 * Route guard that requires an active authenticated session.
 */
export const RequireAuth: React.FC<RequireAuthProps> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

interface RequirePermissionProps {
  permission?: string;
  anyOf?: string[];
  allOf?: string[];
  children: React.ReactNode;
}

/**
 * Route guard that evaluates fine-grained action permissions.
 * Redirects to the AccessDeniedPage with contextual state if authorization fails.
 */
export const RequirePermission: React.FC<RequirePermissionProps> = ({
  permission,
  anyOf,
  allOf,
  children,
}) => {
  const { can, canAny, canAll } = useAuthorization();
  const location = useLocation();

  if (permission && !can(permission)) {
    return (
      <Navigate
        to={ROUTES.ACCESS_DENIED}
        state={{
          requiredPermission: permission,
          fromPath: location.pathname,
          errorCode: 'AUTH_PERMISSION_DENIED',
        }}
        replace
      />
    );
  }

  if (anyOf && anyOf.length > 0 && !canAny(anyOf)) {
    return (
      <Navigate
        to={ROUTES.ACCESS_DENIED}
        state={{
          requiredPermission: anyOf.join(' OR '),
          fromPath: location.pathname,
          errorCode: 'AUTH_PERMISSION_DENIED',
        }}
        replace
      />
    );
  }

  if (allOf && allOf.length > 0 && !canAll(allOf)) {
    return (
      <Navigate
        to={ROUTES.ACCESS_DENIED}
        state={{
          requiredPermission: allOf.join(' AND '),
          fromPath: location.pathname,
          errorCode: 'AUTH_PERMISSION_DENIED',
        }}
        replace
      />
    );
  }

  return <>{children}</>;
};

interface RequireRoleProps {
  allowedRoles?: UserRole[];
  minRole?: UserRole;
  children: React.ReactNode;
}

/**
 * Route guard that checks user roles against allowed roles or minimum hierarchy level.
 */
export const RequireRole: React.FC<RequireRoleProps> = ({
  allowedRoles,
  minRole,
  children,
}) => {
  const { isRole, isAtLeast } = useAuthorization();
  const location = useLocation();

  if (allowedRoles && allowedRoles.length > 0 && !isRole(allowedRoles)) {
    return (
      <Navigate
        to={ROUTES.ACCESS_DENIED}
        state={{
          requiredRole: allowedRoles.join(', '),
          fromPath: location.pathname,
          errorCode: 'AUTH_ROLE_REQUIRED',
        }}
        replace
      />
    );
  }

  if (minRole && !isAtLeast(minRole)) {
    return (
      <Navigate
        to={ROUTES.ACCESS_DENIED}
        state={{
          requiredRole: minRole,
          fromPath: location.pathname,
          errorCode: 'AUTH_ROLE_REQUIRED',
        }}
        replace
      />
    );
  }

  return <>{children}</>;
};
