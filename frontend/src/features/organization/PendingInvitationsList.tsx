import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { invitationService } from '@/services/invitationService';
import { formatDate } from '@/utils/formatters';
import {
  Mail,
  Copy,
  Check,
  Trash2,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Inbox,
} from 'lucide-react';
import type { InvitationResponse } from '@/types/invitation';

interface PendingInvitationsListProps {
  refreshTrigger?: number;
}

export const PendingInvitationsList: React.FC<PendingInvitationsListProps> = ({
  refreshTrigger = 0,
}) => {
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchInvitations = React.useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await invitationService.listInvitations(0, 100);
      setInvitations(res.data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to load invitations.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInvitations();
  }, [fetchInvitations, refreshTrigger]);

  const handleCopyLink = (token: string) => {
    const inviteUrl = `${window.location.origin}/invitations/accept?token=${token}`;
    navigator.clipboard.writeText(inviteUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  const handleRevoke = async (id: string) => {
    try {
      await invitationService.revokeInvitation(id);
      await fetchInvitations();
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } };
      setErrorMessage(
        errorObj?.response?.data?.error?.message || 'Failed to revoke invitation.'
      );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return (
          <Badge variant="pending" className="flex items-center gap-1">
            <Clock className="w-3 h-3" /> Pending
          </Badge>
        );
      case 'ACCEPTED':
        return (
          <Badge variant="success" className="flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Accepted
          </Badge>
        );
      case 'REVOKED':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <XCircle className="w-3 h-3" /> Revoked
          </Badge>
        );
      case 'EXPIRED':
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="w-3 h-3" /> Expired
          </Badge>
        );
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse h-16 bg-muted/40" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {errorMessage && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 flex items-center gap-2 text-destructive text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {invitations.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground border-dashed">
          <Inbox className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="font-medium text-base text-foreground">No active invitations</p>
          <p className="text-xs mt-1">
            Send an invitation to bring new members into your organization.
          </p>
        </Card>
      ) : (
        <div className="space-y-2">
          {invitations.map((inv) => (
            <Card key={inv.id} className="p-4 hover:border-primary/40 transition-colors">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <Mail className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-foreground">{inv.email}</span>
                      <Badge variant="outline" className="text-xs">
                        {inv.role}
                      </Badge>
                      {getStatusBadge(inv.status)}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5 flex items-center gap-3">
                      <span>Sent {formatDate(inv.created_at)}</span>
                      <span>•</span>
                      <span>Expires {formatDate(inv.expires_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  {inv.status === 'PENDING' && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-8"
                        onClick={() => handleCopyLink(inv.token)}
                      >
                        {copiedToken === inv.token ? (
                          <>
                            <Check className="w-3.5 h-3.5 mr-1 text-emerald-500" /> Copied Link
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5 mr-1" /> Copy Link
                          </>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 text-destructive hover:bg-destructive/10 text-xs"
                        onClick={() => handleRevoke(inv.id)}
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-1" /> Revoke
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default PendingInvitationsList;
