import React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { RoleBadge } from './RoleBadge';
import { useAuthorization } from '@/hooks/useAuthorization';
import type { UserRole } from '@/types/auth';
import { ROLE_PERMISSIONS_MAP } from '@/types/permission';
import { RotateCcw, Check, Sparkles } from 'lucide-react';

export interface RoleSwitcherModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ROLES: { role: UserRole; title: string; description: string }[] = [
  {
    role: 'SuperAdmin',
    title: 'Super Administrator',
    description: 'Universal cross-tenant authority, organization provisioning, full administrative control.',
  },
  {
    role: 'OrgAdmin',
    title: 'Organization Admin',
    description: 'Tenant management, department setup, member roles & permissions, AI configurations, security audit logs.',
  },
  {
    role: 'Manager',
    title: 'Project Manager',
    description: 'Project creation, team leadership, document deletion, meeting orchestration, invitation sending.',
  },
  {
    role: 'Member',
    title: 'Employee / Member',
    description: 'Standard collaborator. Document uploads, project participation, semantic search, AI assistant chat.',
  },
  {
    role: 'Viewer',
    title: 'Read-Only Viewer',
    description: 'Restricted access. Knowledge reading, search queries, executive summary dashboard inspection.',
  },
];

export const RoleSwitcherModal: React.FC<RoleSwitcherModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { role, isSimulating, setSimulatedRole, user } = useAuthorization();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="RBAC Role Simulator & Preview"
      className="max-w-xl"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3.5 text-xs text-muted-foreground">
          <Sparkles className="h-5 w-5 shrink-0 text-primary mt-0.5" />
          <div>
            <span className="font-semibold text-foreground">Interactive RBAC Testing Tool:</span>{' '}
            Switch roles instantly to preview conditional navigation, permission-gated action buttons,
            and authorization boundaries in real time without creating separate login credentials.
          </div>
        </div>

        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="text-xs text-muted-foreground">
            Current Active Role:{' '}
            <span className="font-semibold text-foreground">{role}</span>{' '}
            {isSimulating && (
              <span className="ml-1.5 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                Simulated
              </span>
            )}
          </div>
          {isSimulating && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSimulatedRole(null);
                onClose();
              }}
              className="h-7 text-xs gap-1"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset to Actual ({user?.role || 'Member'})
            </Button>
          )}
        </div>

        <div className="grid gap-2.5">
          {ROLES.map((item) => {
            const isSelected = role === item.role;
            const permCount = ROLE_PERMISSIONS_MAP[item.role]?.size ?? 0;

            return (
              <div
                key={item.role}
                onClick={() => {
                  setSimulatedRole(item.role);
                  onClose();
                }}
                className={`flex cursor-pointer items-start justify-between rounded-lg border p-3.5 transition-all hover:border-primary/50 hover:bg-muted/40 ${
                  isSelected
                    ? 'border-primary bg-primary/5 shadow-2xs'
                    : 'border-border bg-card'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <RoleBadge role={item.role} size="sm" />
                    <span className="text-sm font-semibold text-foreground">
                      {item.title}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      ({permCount} permissions)
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </div>

                <div className="ml-3 shrink-0 pt-1">
                  {isSelected ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      <Check className="h-3 w-3" />
                    </div>
                  ) : (
                    <div className="h-5 w-5 rounded-full border border-border" />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end pt-2 border-t border-border">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};
