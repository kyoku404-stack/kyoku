import React from 'react';
import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon, Laptop } from 'lucide-react';

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <div className="flex items-center rounded-lg border border-border bg-muted/40 p-1">
      <button
        onClick={() => setTheme('light')}
        className={`flex items-center justify-center rounded-md p-1.5 transition-colors ${
          theme === 'light'
            ? 'bg-card text-foreground shadow-xs'
            : 'text-muted-foreground hover:text-foreground'
        }`}
        title="Light Mode"
        aria-label="Light Mode"
      >
        <Sun className="h-4 w-4" />
      </button>

      <button
        onClick={() => setTheme('dark')}
        className={`flex items-center justify-center rounded-md p-1.5 transition-colors ${
          theme === 'dark'
            ? 'bg-card text-foreground shadow-xs'
            : 'text-muted-foreground hover:text-foreground'
        }`}
        title="Dark Mode"
        aria-label="Dark Mode"
      >
        <Moon className="h-4 w-4" />
      </button>

      <button
        onClick={() => setTheme('system')}
        className={`flex items-center justify-center rounded-md p-1.5 transition-colors ${
          theme === 'system'
            ? 'bg-card text-foreground shadow-xs'
            : 'text-muted-foreground hover:text-foreground'
        }`}
        title={`System (${resolvedTheme})`}
        aria-label="System Theme"
      >
        <Laptop className="h-4 w-4" />
      </button>
    </div>
  );
};
