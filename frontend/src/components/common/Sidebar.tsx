import React from 'react';
import { NavLink } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { useUIStore } from '@/store/useUIStore';
import {
  LayoutDashboard,
  Search,
  UploadCloud,
  MessageSquare,
  FolderKanban,
  Video,
  BarChart3,
  Activity,
  X,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navItems: NavItem[] = [
  { label: 'Overview', path: ROUTES.HOME, icon: LayoutDashboard },
  { label: 'Semantic Search', path: ROUTES.SEARCH, icon: Search },
  { label: 'Document Ingestion', path: ROUTES.UPLOAD, icon: UploadCloud },
  { label: 'RAG Knowledge Chat', path: ROUTES.CHAT, icon: MessageSquare },
  { label: 'Projects & Hubs', path: ROUTES.PROJECTS, icon: FolderKanban },
  { label: 'Meeting Intelligence', path: ROUTES.MEETINGS, icon: Video },
  { label: 'Analytics & Graph', path: ROUTES.ANALYTICS, icon: BarChart3 },
  { label: 'System Health', path: ROUTES.HEALTH, icon: Activity, badge: 'Live' },
];

export const Sidebar: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

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
            {navItems.map((item) => (
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
                  <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="border-t border-border p-4">
          <div className="rounded-lg bg-muted/40 p-3 text-xs text-muted-foreground">
            <div className="font-medium text-foreground">KEEP Platform</div>
            <div className="mt-0.5">Phase 1.1 Architecture Baseline</div>
          </div>
        </div>
      </aside>
    </>
  );
};
