import React from 'react';
import type { UserProfileResponse } from '@/types/auth';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { User, Mail, Building, ShieldCheck, Calendar, CheckCircle2, XCircle } from 'lucide-react';
import { formatDate } from '@/utils/formatters';

interface UserProfileViewProps {
  user: UserProfileResponse | null;
  loading?: boolean;
}

export const UserProfileView: React.FC<UserProfileViewProps> = ({ user, loading = false }) => {
  if (loading) {
    return <Card className="p-8 animate-pulse bg-muted/40 h-64" />;
  }

  if (!user) {
    return (
      <Card className="p-8 text-center text-muted-foreground border-dashed">
        <User className="w-12 h-12 mx-auto mb-3 opacity-40 text-primary" />
        <p className="font-medium text-lg text-foreground">No Profile Available</p>
        <p className="text-sm mt-1">Authenticate to view user profile details and RBAC permissions.</p>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary/10 text-primary font-bold text-lg flex items-center justify-center">
            {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              {user.full_name}
              <Badge variant="processed">{user.role}</Badge>
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              User ID: {user.id}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-border">
          <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/20">
            <Mail className="w-4 h-4 text-primary shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase">Email Address</p>
              <p className="text-xs font-medium text-foreground">{user.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/20">
            <Building className="w-4 h-4 text-primary shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase">Organization UUID</p>
              <p className="text-xs font-mono text-foreground">{user.organization_id}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/20">
            <ShieldCheck className="w-4 h-4 text-primary shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase">RBAC Role</p>
              <p className="text-xs font-semibold text-foreground">{user.role}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/20">
            <Calendar className="w-4 h-4 text-primary shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase">Member Since</p>
              <p className="text-xs font-medium text-foreground">{formatDate(user.created_at)}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs pt-2">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-muted-foreground">Account Status:</span>
            {user.is_active ? (
              <Badge variant="success" className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Active
              </Badge>
            ) : (
              <Badge variant="destructive" className="flex items-center gap-1">
                <XCircle className="w-3 h-3" /> Suspended
              </Badge>
            )}
          </div>

          {user.is_verified !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-muted-foreground">Email Status:</span>
              {user.is_verified ? (
                <Badge variant="processed" className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Verified
                </Badge>
              ) : (
                <Badge variant="pending">Unverified</Badge>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
