import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { useUIStore } from '@/store/useUIStore';
import { useAuthorization } from '@/hooks/useAuthorization';
import { Permission } from '@/types/permission';
import type { UserRole } from '@/types/auth';
import { RoleBadge } from '@/components/authorization/RoleBadge';
import { RoleSwitcherModal } from '@/components/authorization/RoleSwitcherModal';
import {
  LayoutDashboard,
  Search,
  UploadCloud,
  MessageSquare,
  Building2,
  FolderKanban,
  Users,
  Video,
  BarChart3,
  Activity,
  ShieldCheck,
  Sparkles,
  X,
  FileStack,
  Cpu,
  Bot,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  requiredPermission?: string;
  minRole?: UserRole;
}

const navItems: NavItem[] = [
  { label: 'Overview', path: ROUTES.HOME, icon: LayoutDashboard },
  { label: 'Organization & Teams', path: ROUTES.ORGANIZATION, icon: Building2 },
  { label: 'Workspaces & Projects', path: ROUTES.PROJECTS, icon: FolderKanban },
  { label: 'Members & Access', path: ROUTES.MEMBERS, icon: Users, requiredPermission: Permission.MEMBER_READ },
  { label: 'Semantic Search', path: ROUTES.SEARCH, icon: Search, requiredPermission: Permission.AI_SEARCH },
  {
    label: 'Knowledge Repository',
    path: ROUTES.DOCUMENTS,
    icon: FileStack,
    requiredPermission: Permission.DOCUMENT_CREATE,
    badge: 'New',
  },
  {
    label: 'AI Ingestion Pipeline',
    path: ROUTES.INGESTION,
    icon: Cpu,
    requiredPermission: Permission.DOCUMENT_CREATE,
    badge: 'Phase 2.1',
  },
  { label: 'Document Upload', path: ROUTES.UPLOAD, icon: UploadCloud, requiredPermission: Permission.DOCUMENT_CREATE },
  { label: 'RAG Knowledge Chat', path: ROUTES.CHAT, icon: MessageSquare, requiredPermission: Permission.AI_CHAT, badge: 'Phase 2.2' },
  { label: 'Enterprise AI Assistant', path: ROUTES.ASSISTANT, icon: Bot, requiredPermission: Permission.AI_CHAT, badge: 'Phase 2.3' },
  { label: 'Meeting Intelligence', path: ROUTES.MEETINGS, icon: Video },
  { label: 'Analytics & Graph', path: ROUTES.ANALYTICS, icon: BarChart3, requiredPermission: Permission.ANALYTICS_VIEW },
  {
    label: 'Security Audit Logs',
    path: ROUTES.AUDIT_LOGS,
    icon: ShieldCheck,
    requiredPermission: Permission.AUDIT_READ,
    badge: 'RBAC',
  },
  {
    label: 'Observability & Health',
    path: ROUTES.OBSERVABILITY,
    icon: Activity,
    badge: 'Live',
  },
];


export const Sidebar: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const { can, isAtLeast, role, isSimulating } = useAuthorization();
  const [switcherOpen, setSwitcherOpen] = useState(false);

  // Filter items based on user's active permissions/role
  const visibleNavItems = navItems.filter((item) => {
    if (item.requiredPermission && !can(item.requiredPermission)) {
      return false;
    }
    if (item.minRole && !isAtLeast(item.minRole)) {
      return false;
    }
    return true;
  });

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-xs md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card transition-transform duration-200 ease-in-out md:static md:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-border md:hidden">
          <span className="font-bold text-lg text-foreground">Navigation</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-1 flex-col overflow-y-auto px-4 py-6">
          <div className="mb-4 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Platform Modules
          </div>

          <nav className="space-y-1.5">
            {visibleNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (window.innerWidth < 768) setSidebarOpen(false);
                }}
                className={({ isActive }) =>
                  cn(
                    'flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary font-semibold'
                      : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                  )
                }
              >
                <div className="flex items-center space-x-3">
                  <item.icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      'rounded-full px-2 py-0.5 text-[10px] font-semibold',
                      item.badge === 'RBAC'
                        ? 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'
                        : item.badge === 'New'
                          ? 'bg-violet-500/10 text-violet-600 dark:text-violet-400'
                          : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Role & Access Status in Footer */}
        <div className="border-t border-border p-4 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Active Role
            </span>
            <button
              onClick={() => setSwitcherOpen(true)}
              className="flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
              title="Preview UI under different roles"
            >
              <Sparkles className="h-3 w-3" />
              <span>Simulate</span>
            </button>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-muted/40 p-2.5">
            <div className="flex items-center gap-2">
              <RoleBadge role={role} size="sm" />
              {isSimulating && (
                <span className="text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                  (Sim)
                </span>
              )}
            </div>
            <span className="text-[10px] text-muted-foreground">Phase 1.9</span>
          </div>
        </div>
      </aside>


      <RoleSwitcherModal
        isOpen={switcherOpen}
        onClose={() => setSwitcherOpen(false)}
      />
    </>
  );
};
