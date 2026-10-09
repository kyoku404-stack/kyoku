import React, { useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { UserProfileView } from '@/features/auth/UserProfileView';
import { ChangePasswordForm } from '@/features/auth/ChangePasswordForm';
import { Button } from '@/components/ui/button';
import { User, Lock } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, isLoading } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'security'>('profile');

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Account & Identity Settings
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your user profile, RBAC permissions, and authentication credentials.
          </p>
        </div>

        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border">
          <Button
            size="sm"
            variant={activeTab === 'profile' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('profile')}
            className="text-xs flex items-center gap-1.5"
          >
            <User className="w-3.5 h-3.5" /> Profile
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'security' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('security')}
            className="text-xs flex items-center gap-1.5"
          >
            <Lock className="w-3.5 h-3.5" /> Security
          </Button>
        </div>
      </div>

      {activeTab === 'profile' ? (
        <UserProfileView user={user} loading={isLoading} />
      ) : (
        <div className="max-w-md">
          <ChangePasswordForm />
        </div>
      )}
    </div>
  );
};
