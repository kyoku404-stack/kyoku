import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { RoleBadge } from '@/components/authorization/RoleBadge';
import { RoleSwitcherModal } from '@/components/authorization/RoleSwitcherModal';
import { useAuthorization } from '@/hooks/useAuthorization';
import { ROUTES } from '@/routes/paths';
import {
  ShieldAlert,
  ArrowLeft,
  LayoutDashboard,
  Sparkles,
  Lock,
  HelpCircle,
} from 'lucide-react';

interface AccessDeniedState {
  requiredPermission?: string;
  requiredRole?: string;
  errorCode?: string;
  message?: string;
  fromPath?: string;
}

export const AccessDeniedPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { role, isSimulating } = useAuthorization();
  const [switcherOpen, setSwitcherOpen] = useState(false);

  const state = (location.state as AccessDeniedState) || {};
  const requiredPermission = state.requiredPermission;
  const requiredRole = state.requiredRole;
  const errorCode = state.errorCode || 'AUTH_PERMISSION_DENIED';
  const customMessage = state.message;

  return (
    <div className="flex min-h-[calc(100vh-10rem)] items-center justify-center p-4 sm:p-6">
      <Card className="max-w-xl w-full border-destructive/30 shadow-lg bg-card overflow-hidden">
        <div className="h-2 w-full bg-linear-to-r from-destructive via-amber-500 to-destructive" />

        <CardHeader className="text-center pb-4 pt-6">
          <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive shadow-inner">
            <ShieldAlert className="h-9 w-9" />
          </div>

          <div className="inline-flex items-center gap-1.5 mx-auto rounded-full bg-destructive/10 px-3 py-1 text-xs font-semibold text-destructive mb-2">
            <Lock className="h-3.5 w-3.5" />
            <span>403 Forbidden — {errorCode}</span>
          </div>

          <CardTitle className="text-2xl font-bold tracking-tight text-foreground">
            Access Restricted
          </CardTitle>
          <CardDescription className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
            {customMessage ||
              'Your current organizational role does not possess the requisite permissions to access this view or execute this operation.'}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6 pt-2">
          {/* Metadata Grid */}
          <div className="rounded-xl border border-border bg-muted/30 p-4 space-y-3 text-xs">
            <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
              <span className="text-muted-foreground font-medium">Your Active Role:</span>
              <div className="flex items-center gap-2">
                <RoleBadge role={role} size="sm" />
                {isSimulating && (
                  <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                    Simulated
                  </span>
                )}
              </div>
            </div>

            {requiredPermission && (
              <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
                <span className="text-muted-foreground font-medium">Required Permission:</span>
                <code className="rounded bg-muted px-2 py-0.5 font-mono text-[11px] text-foreground font-semibold">
                  {requiredPermission}
                </code>
              </div>
            )}

            {requiredRole && (
              <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
                <span className="text-muted-foreground font-medium">Minimum Role Required:</span>
                <span className="font-semibold text-foreground">{requiredRole}</span>
              </div>
            )}

            <div className="flex items-start gap-2 pt-1 text-[11px] text-muted-foreground">
              <HelpCircle className="h-4 w-4 shrink-0 text-muted-foreground mt-0.5" />
              <span>
                KEEP enforces least-privilege role boundaries and zero-trust multi-tenancy.
                To request elevated privileges, contact your Organization Administrator.
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2.5 justify-center">
            <Button
              variant="outline"
              onClick={() => {
                if (state.fromPath) {
                  navigate(state.fromPath);
                } else if (window.history.length > 2) {
                  navigate(-1);
                } else {
                  navigate(ROUTES.HOME);
                }
              }}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Go Back
            </Button>

            <Button
              onClick={() => navigate(ROUTES.DASHBOARD)}
              className="gap-2"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard Overview
            </Button>

            <Button
              variant="secondary"
              onClick={() => setSwitcherOpen(true)}
              className="gap-2"
            >
              <Sparkles className="h-4 w-4 text-primary" />
              Switch Role Preview
            </Button>
          </div>
        </CardContent>
      </Card>

      <RoleSwitcherModal
        isOpen={switcherOpen}
        onClose={() => setSwitcherOpen(false)}
      />
    </div>
  );
};
