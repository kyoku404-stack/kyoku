import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import type { UserRole } from '@/types/auth';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const location = useLocation();
  const { isAuthenticated, isLoading, user } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" label="Verifying security credentials..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div className="p-8 text-center max-w-md mx-auto my-12 border border-destructive/30 rounded-lg bg-destructive/10">
        <h2 className="text-lg font-bold text-destructive">403 — Permission Denied</h2>
        <p className="text-xs text-muted-foreground mt-2">
          Your role (<span className="font-semibold text-foreground">{user.role}</span>) does not have authorization to access this resource.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
