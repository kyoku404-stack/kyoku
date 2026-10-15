import React, { useState, useEffect, useRef } from 'react';
import { Search, X, FolderGit2, FileText, User as UserIcon, Users, Loader2, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useGlobalSearch } from '@/hooks/useDashboard';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { GlobalSearchResultItem } from '@/types/dashboard';

interface GlobalSearchBarProps {
  className?: string;
  placeholder?: string;
}

export const GlobalSearchBar: React.FC<GlobalSearchBarProps> = ({
  className = '',
  placeholder = 'Search projects, documents, teams... (Ctrl+K)',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { query, setQuery, results, isSearching, totalCount, clearSearch } = useGlobalSearch(250);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Listen for Ctrl+K or Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectResult = (item: GlobalSearchResultItem) => {
    setIsOpen(false);
    clearSearch();
    if (item.url) {
      navigate(item.url);
    } else {
      switch (item.type) {
        case 'project':
          navigate(`/projects?id=${item.id}`);
          break;
        case 'document':
          navigate(`/documents?id=${item.id}`);
          break;
        case 'user':
        case 'team':
          navigate(`/profile?id=${item.id}`);
          break;
        default:
          break;
      }
    }
  };

  const getItemIcon = (type: GlobalSearchResultItem['type']) => {
    switch (type) {
      case 'project':
        return <FolderGit2 className="h-4 w-4 text-primary" />;
      case 'document':
        return <FileText className="h-4 w-4 text-emerald-500" />;
      case 'user':
        return <UserIcon className="h-4 w-4 text-sky-500" />;
      case 'team':
        return <Users className="h-4 w-4 text-violet-500" />;
      default:
        return <Search className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Search Input Bar */}
      <div className="relative flex items-center">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="w-full h-9 pl-9 pr-14 text-xs sm:text-sm bg-muted/40 hover:bg-muted/70 focus:bg-background border border-border focus:border-primary focus:ring-1 focus:ring-primary rounded-lg transition-colors placeholder:text-muted-foreground text-foreground outline-none"
          aria-label="Global search query"
        />
        {query ? (
          <button
            type="button"
            onClick={() => {
              clearSearch();
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : (
          <kbd className="hidden sm:inline-flex items-center absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] font-mono font-medium text-muted-foreground bg-muted border border-border rounded pointer-events-none">
            Ctrl+K
          </kbd>
        )}
      </div>

      {/* Dropdown Results Card */}
      {isOpen && query.trim().length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl overflow-hidden min-w-[320px] max-w-lg">
          <div className="p-2 border-b border-border/60 bg-muted/30 flex items-center justify-between text-xs text-muted-foreground font-medium">
            <span>
              {isSearching ? (
                <span className="flex items-center gap-1.5 text-primary">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Searching across workspace...
                </span>
              ) : (
                `Found ${totalCount} result${totalCount === 1 ? '' : 's'}`
              )}
            </span>
            <span className="text-[10px]">Press Esc to close</span>
          </div>

          <div className="max-h-[380px] overflow-y-auto divide-y divide-border/30">
            {isSearching && results.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin mx-auto text-primary mb-2" />
                Querying projects, documents, and teams...
              </div>
            ) : results.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                No matching results for &ldquo;{query}&rdquo;
              </div>
            ) : (
              results.map((item) => (
                <div
                  key={`${item.type}-${item.id}`}
                  onClick={() => handleSelectResult(item)}
                  className="p-3 hover:bg-muted/60 cursor-pointer transition-colors flex items-start justify-between gap-3 group"
                >
                  <div className="flex items-start gap-2.5 min-w-0">
                    <div className="mt-0.5 p-1 rounded-md bg-muted group-hover:bg-background border border-border">
                      {getItemIcon(item.type)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                          {item.title}
                        </span>
                        <Badge variant="outline" className="text-[10px] uppercase font-mono px-1 py-0 h-4">
                          {item.type}
                        </Badge>
                      </div>
                      {item.subtitle && (
                        <p className="text-xs text-muted-foreground truncate mt-0.5">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </div>

                  <ArrowRight className="h-4 w-4 text-muted-foreground/40 group-hover:text-primary transition-colors shrink-0 mt-1 opacity-0 group-hover:opacity-100" />
                </div>
              ))
            )}
          </div>

          <div className="p-2 border-t border-border/60 bg-muted/20 text-center">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary hover:text-primary/90 w-full h-7"
              onClick={() => {
                setIsOpen(false);
                navigate(`/search?q=${encodeURIComponent(query)}`);
              }}
            >
              Advanced Search for &ldquo;{query}&rdquo;
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
