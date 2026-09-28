import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-border bg-card/40 py-6 px-4 sm:px-6">
      <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-muted-foreground max-w-7xl mx-auto gap-2">
        <div>
          &copy; {new Date().getFullYear()} KEEP (Knowledge Extraction & Enterprise Platform). All rights reserved.
        </div>
        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center">
            <span className="h-2 w-2 rounded-full bg-emerald-500 mr-1.5" />
            FastAPI + React 18
          </span>
          <span>•</span>
          <span>Multi-Tenant Architecture</span>
        </div>
      </div>
    </footer>
  );
};
