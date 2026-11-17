import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { ThemeToggle } from './ThemeToggle';
import { useUIStore } from '@/store/useUIStore';
import { useAuthStore } from '@/store/useAuthStore';
import { useAuthorization } from '@/hooks/useAuthorization';
import { RoleBadge } from '@/components/authorization/RoleBadge';
import { Menu, Layers, ShieldCheck, Activity, User as UserIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

import { GlobalSearchBar, NotificationCenter } from '@/features/dashboard';

export const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const { role } = useAuthorization();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/80 backdrop-blur-md overflow-x-hidden">
      <div className="flex h-16 items-center justify-between px-3 sm:px-6 gap-2 sm:gap-3 max-w-full">
        <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="md:hidden"
            aria-label="Toggle menu"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <Link to={ROUTES.HOME} className="flex items-center space-x-2 sm:space-x-2.5">
            <div className="flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm shrink-0">
              <Layers className="h-4 w-4 sm:h-5 sm:w-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-foreground text-base sm:text-lg leading-none">
                KEEP
              </span>
              <span className="hidden sm:block text-[10px] text-muted-foreground tracking-wider uppercase font-medium">
                Enterprise AI
              </span>
            </div>
          </Link>
        </div>

        {/* Center Global Search (Phase 1.7) */}
        {isAuthenticated && (
          <div className="hidden md:flex flex-1 max-w-md mx-4">
            <GlobalSearchBar className="w-full" />
          </div>
        )}

        {/* Center / Right actions */}
        <div className="flex items-center space-x-1.5 sm:space-x-3 shrink-0">
          <Link to={ROUTES.HEALTH} className="hidden lg:flex items-center">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <Activity className="h-4 w-4 mr-1.5 text-emerald-500" />
              <span>Engine Status</span>
            </Button>
          </Link>

          {isAuthenticated && (
            <>
              <div className="h-4 w-px bg-border hidden lg:block" />
              <NotificationCenter />
            </>
          )}

          <div className="hidden sm:flex">
            <ThemeToggle />
          </div>

          {isAuthenticated ? (
            <div className="flex items-center gap-1.5 sm:gap-2.5">
              <div className="hidden sm:block">
                <RoleBadge role={role} size="sm" />
              </div>
              <Link to={ROUTES.PROFILE} className="flex items-center gap-1.5 text-xs font-medium text-foreground hover:underline">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <UserIcon className="h-4 w-4" />
                </div>
                <span className="hidden xl:inline max-w-[120px] truncate">
                  {user?.full_name || user?.email || 'Profile'}
                </span>
              </Link>
            </div>
          ) : (
            <Link to={ROUTES.LOGIN}>
              <Button variant="outline" size="sm">
                <ShieldCheck className="h-4 w-4 mr-1.5" />
                Sign In
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};
