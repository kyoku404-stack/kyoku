import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuthStore } from '@/store/useAuthStore';
import { ROUTES } from '@/routes/paths';
import { LogIn, KeyRound } from 'lucide-react';
import type { UserRole } from '@/types/auth';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [email, setEmail] = useState('demo.lead@enterprise.com');
  const [password, setPassword] = useState('DemoSecurePassword123!');
  const [role, setRole] = useState<UserRole>('OrgAdmin');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      setAuth(
        {
          id: 'user_demo_123',
          organization_id: 'org_acme_corp_456',
          email,
          full_name: 'Alex Rivera',
          role,
          is_active: true,
          created_at: new Date().toISOString(),
        },
        'mock_jwt_access_token_phase_1_1'
      );
      setLoading(false);
      navigate(ROUTES.HOME);
    }, 600);
  };

  return (
    <Card className="shadow-lg border border-border">
      <CardHeader className="space-y-1">
        <CardTitle className="text-xl font-bold">Sign In to KEEP</CardTitle>
        <CardDescription>
          Enter enterprise credentials or test with standard mock profiles.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Work Email
            </label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@organization.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Password
            </label>
            <Input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Select Demo Role (RBAC Simulation)
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="SuperAdmin">SuperAdmin (Platform-wide)</option>
              <option value="OrgAdmin">OrgAdmin (Organization Lead)</option>
              <option value="Manager">Manager (Team / Department)</option>
              <option value="Member">Member (Standard Contributor)</option>
              <option value="Guest">Guest (Read-Only)</option>
            </select>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-3">
          <Button type="submit" className="w-full" isLoading={loading}>
            <LogIn className="mr-2 h-4 w-4" />
            Sign In with Credentials
          </Button>

          <div className="flex items-center justify-center space-x-1 text-xs text-muted-foreground">
            <KeyRound className="h-3.5 w-3.5" />
            <span>Full SSO & OAuth integration scheduled for Phase 1.4</span>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
};
