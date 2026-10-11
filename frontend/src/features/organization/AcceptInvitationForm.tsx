import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { invitationService } from '@/services/invitationService';
import { CheckCircle2, AlertCircle, KeyRound, User, Lock, ArrowRight } from 'lucide-react';
import type { InvitationAccept } from '@/types/invitation';

interface AcceptInvitationFormProps {
  initialToken?: string;
  onSuccess?: () => void;
}

export const AcceptInvitationForm: React.FC<AcceptInvitationFormProps> = ({
  initialToken = '',
  onSuccess,
}) => {
  const [token, setToken] = useState(initialToken);
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [isAccepted, setIsAccepted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);
    const payload: InvitationAccept = {
      token: token.trim(),
      full_name: fullName.trim(),
      password,
    };

    try {
      await invitationService.acceptInvitation(payload);
      setIsAccepted(true);
      onSuccess?.();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setErrorMessage(
        errorObj?.response?.data?.error?.message ||
          errorObj?.message ||
          'Failed to accept invitation. The link may have expired or is invalid.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (isAccepted) {
    return (
      <Card className="max-w-md mx-auto text-center p-6 shadow-lg">
        <div className="w-14 h-14 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <CardTitle className="text-xl font-bold mb-2">Welcome to KEEP!</CardTitle>
        <CardDescription className="mb-6">
          Your account has been successfully initialized and activated in the organization workspace.
        </CardDescription>
        <Button
          variant="primary"
          className="w-full"
          onClick={() => (window.location.href = '/auth/login')}
        >
          Proceed to Login <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </Card>
    );
  }

  return (
    <Card className="max-w-md mx-auto shadow-lg">
      <CardHeader>
        <div className="flex items-center gap-2">
          <KeyRound className="w-6 h-6 text-primary" />
          <CardTitle className="text-xl">Accept Workspace Invitation</CardTitle>
        </div>
        <CardDescription>
          Join your enterprise team workspace by confirming your profile and setting a secure password.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-2 text-destructive text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Invitation Token *
            </label>
            <Input
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste invitation token"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Full Legal Name *
            </label>
            <div className="relative">
              <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                className="pl-9"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Create Password *
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="pl-9"
                required
              />
            </div>
            <p className="text-[11px] text-muted-foreground mt-1">
              Minimum 8 characters with at least one number and uppercase letter.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Confirm Password *
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="pl-9"
                required
              />
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            isLoading={loading}
            disabled={!token.trim() || !fullName.trim() || !password}
          >
            Activate Account & Join <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default AcceptInvitationForm;
