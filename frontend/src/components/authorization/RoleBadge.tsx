import React from 'react';
import type { UserRole } from '@/types/auth';
import { ShieldAlert, ShieldCheck, UserCheck, Eye, Shield, Users } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface RoleBadgeProps {
  role: UserRole;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({
  role,
  size = 'md',
  showIcon = true,
  className,
}) => {
  const config: Record<
    UserRole,
    { label: string; icon: React.ComponentType<{ className?: string }>; colorClasses: string }
  > = {
    SuperAdmin: {
      label: 'Super Admin',
      icon: ShieldAlert,
      colorClasses: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20',
    },
    OrgAdmin: {
      label: 'Org Admin',
      icon: ShieldCheck,
      colorClasses: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20',
    },
    Manager: {
      label: 'Manager',
      icon: Shield,
      colorClasses: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
    },
    Member: {
      label: 'Member',
      icon: UserCheck,
      colorClasses: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    },
    Viewer: {
      label: 'Viewer',
      icon: Eye,
      colorClasses: 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20',
    },
    Guest: {
      label: 'Guest',
      icon: Users,
      colorClasses: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    },
  };

  const item = config[role] ?? config.Member;
  const Icon = item.icon;

  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3 py-1.5 gap-2',
  }[size];

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
    lg: 'h-4 w-4',
  }[size];

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border shadow-2xs',
        item.colorClasses,
        sizeClasses,
        className
      )}
    >
      {showIcon && <Icon className={cn('shrink-0', iconSizes)} />}
      <span>{item.label}</span>
    </span>
  );
};
