import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { Layers } from 'lucide-react';
import { ThemeToggle } from '@/components/common/ThemeToggle';

export const AuthLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/20 p-4 sm:p-6">
      <div className="absolute top-6 right-6">
        <ThemeToggle />
      </div>

      <div className="mb-6 flex flex-col items-center">
        <Link to={ROUTES.HOME} className="flex items-center space-x-2.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md">
            <Layers className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-foreground">KEEP</span>
        </Link>
        <p className="mt-2 text-sm text-muted-foreground">Knowledge Extraction & Enterprise Platform</p>
      </div>

      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>
  );
};
