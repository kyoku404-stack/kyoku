/**
 * Phase 3.2 WorkspaceGrid Component.
 * Displays all team workspaces available to the user with search and filtering.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Users,
  Search,
  Lock,
  Globe,
  ChevronRight,
  Shield,
  Layers,
} from 'lucide-react';
import type { WorkspaceSummary } from '@/types/collaboration';

interface WorkspaceGridProps {
  workspaces: WorkspaceSummary[];
  activeWorkspaceId?: string;
  onSelectWorkspace: (workspaceId: string) => void;
  onCreateClick: () => void;
}

export const WorkspaceGrid: React.FC<WorkspaceGridProps> = ({
  workspaces,
  activeWorkspaceId,
  onSelectWorkspace,
  onCreateClick,
}) => {
  const [query, setQuery] = useState('');

  const filtered = workspaces.filter(
    (w) =>
      w.name.toLowerCase().includes(query.toLowerCase()) ||
      w.slug.toLowerCase().includes(query.toLowerCase()) ||
      (w.description && w.description.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div className="flex flex-col gap-4">
      {/* Search Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search workspaces..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
          />
        </div>
        <div className="text-xs font-medium text-slate-500 dark:text-slate-400 self-end sm:self-center">
          Showing {filtered.length} of {workspaces.length} workspaces
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <Layers className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No workspaces found
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            {query
              ? 'No workspaces match your query. Try a different search term.'
              : 'Create your first team workspace to start collaborating.'}
          </p>
          <button
            onClick={onCreateClick}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all"
          >
            Create Workspace
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((w) => {
            const isActive = w.id === activeWorkspaceId;
            return (
              <div
                key={w.id}
                onClick={() => onSelectWorkspace(w.id)}
                className={`group relative p-5 rounded-2xl bg-white dark:bg-slate-900 border transition-all cursor-pointer flex flex-col justify-between hover:shadow-md ${
                  isActive
                    ? 'border-indigo-600 dark:border-indigo-500 ring-2 ring-indigo-500/20'
                    : 'border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div>
                  {/* Top pill & avatar */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-sm"
                      style={{ backgroundColor: w.avatar_color || '#4F46E5' }}
                    >
                      {w.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 flex items-center gap-1">
                        <Shield className="w-3 h-3 text-indigo-500" />
                        {w.current_user_role}
                      </span>
                      {w.is_private ? (
                        <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-300">
                          <Lock className="w-3 h-3" />
                        </span>
                      ) : (
                        <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-300">
                          <Globe className="w-3 h-3" />
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Title & Description */}
                  <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    {w.name}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5 mb-2">
                    /{w.slug}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mb-4">
                    {w.description || 'No description provided.'}
                  </p>
                </div>

                {/* Footer stats */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    {w.member_count} {w.member_count === 1 ? 'member' : 'members'}
                  </span>
                  <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
                    {isActive ? 'Current' : 'Select'}
                    <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
