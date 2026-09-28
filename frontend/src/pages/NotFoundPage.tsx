import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/routes/paths';
import { Button } from '@/components/ui/button';
import { Home, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center p-6">
      <div className="rounded-full bg-primary/10 p-6 text-primary mb-6">
        <span className="text-5xl font-extrabold tracking-tight">404</span>
      </div>
      <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
        Page Not Found
      </h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        The requested resource or endpoint does not exist or has been relocated within the KEEP platform.
      </p>
      <div className="mt-6 flex items-center space-x-3">
        <Link to={ROUTES.HOME}>
          <Button>
            <Home className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </Link>
        <Button variant="outline" onClick={() => window.history.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go Back
        </Button>
      </div>
    </div>
  );
};
