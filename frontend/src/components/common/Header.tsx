import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { ThemeToggle } from './ThemeToggle';
import { useUIStore } from '@/store/useUIStore';
import { Menu, Layers, ShieldCheck, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="md:hidden"
            aria-label="Toggle menu"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <Link to={ROUTES.HOME} className="flex items-center space-x-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <Layers className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-foreground text-lg leading-none">
                KEEP
              </span>
              <span className="text-[10px] text-muted-foreground tracking-wider uppercase font-medium">
                Enterprise AI
              </span>
            </div>
          </Link>
        </div>

        {/* Center / Right actions */}
        <div className="flex items-center space-x-3">
          <Link to={ROUTES.HEALTH} className="hidden sm:flex items-center">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <Activity className="h-4 w-4 mr-1.5 text-emerald-500" />
              <span>Engine Status</span>
            </Button>
          </Link>

          <div className="h-4 w-px bg-border hidden sm:block" />

          <ThemeToggle />

          <Link to={ROUTES.LOGIN}>
            <Button variant="outline" size="sm">
              <ShieldCheck className="h-4 w-4 mr-1.5" />
              Sign In
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
};
