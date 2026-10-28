/**
 * Phase 3.2 WorkspaceHeader Component.
 * Displays current workspace identity, presence indicators, KPIs, and quick actions.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  Users,
  MessageSquare,
  FolderGit2,
  Lock,
  Globe,
  Plus,
  RefreshCw,
  Clock,
  Sparkles,
} from 'lucide-react';
import type {
  PresenceCollaborator,
  WorkspaceDashboardData,
  WorkspaceDetail,
} from '@/types/collaboration';

interface WorkspaceHeaderProps {
  workspace: WorkspaceDetail | null;
  dashboard: WorkspaceDashboardData | null;
  collaborators: PresenceCollaborator[];
  onCreateClick: () => void;
  onRefreshClick: () => void;
  onToggleActivityFeed: () => void;
  isLoading: boolean;
}

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({
  workspace,
  dashboard,
  collaborators,
  onCreateClick,
  onRefreshClick,
  onToggleActivityFeed,
  isLoading,
}) => {
  return (
    <div className="flex flex-col gap-5">
      {/* Top Action Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-indigo-500/20"
            style={{ backgroundColor: workspace?.avatar_color || '#4F46E5' }}
          >
            {workspace?.name ? workspace.name.charAt(0).toUpperCase() : 'W'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {workspace?.name || 'Team Workspaces'}
              </h1>
              {workspace?.is_private ? (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 font-medium border border-amber-200/50">
                  <Lock className="w-3 h-3" /> Private
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-medium border border-emerald-200/50">
                  <Globe className="w-3 h-3" /> Shared
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              {workspace?.description ||
                'Collaborative team workspaces for projects, discussions, and organizational knowledge.'}
            </p>
          </div>
        </div>

        {/* Buttons & Presence Avatars */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Active Collaborator Avatar Cluster */}
          {collaborators.length > 0 && (
            <div className="flex items-center bg-white dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm mr-1">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 mr-2 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Live:
              </span>
              <div className="flex -space-x-2 overflow-hidden">
                {collaborators.slice(0, 4).map((c) => (
                  <div
                    key={c.user_id}
                    className="relative inline-block w-7 h-7 rounded-full ring-2 ring-white dark:ring-slate-900 bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-xs font-bold flex items-center justify-center cursor-pointer"
                    title={`${c.full_name} (${c.status})`}
                  >
                    {c.full_name.charAt(0).toUpperCase()}
                    <span
                      className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ring-1 ring-white ${
                        c.status === 'EDITING'
                          ? 'bg-blue-500'
                          : c.status === 'AWAY'
                            ? 'bg-amber-400'
                            : 'bg-emerald-500'
                      }`}
                    />
                  </div>
                ))}
                {collaborators.length > 4 && (
                  <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-semibold flex items-center justify-center ring-2 ring-white dark:ring-slate-900">
                    +{collaborators.length - 4}
                  </div>
                )}
              </div>
            </div>
          )}

          <button
            onClick={onToggleActivityFeed}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-all shadow-sm"
          >
            <Clock className="w-4 h-4 text-slate-500" />
            Activity
          </button>

          <button
            onClick={onRefreshClick}
            disabled={isLoading}
            className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-all shadow-sm"
            title="Refresh Collaboration State"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={onCreateClick}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-500/25 transition-all"
          >
            <Plus className="w-4 h-4" />
            New Workspace
          </button>
        </div>
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {dashboard?.active_members_count ?? workspace?.member_count ?? 1}
            </div>
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Active Members
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-950/50 flex items-center justify-center text-purple-600 dark:text-purple-400">
            <FolderGit2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {dashboard?.active_projects_count ?? 0}
            </div>
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Shared Projects
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {dashboard?.open_discussions_count ?? 0}
            </div>
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Open Discussions
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {dashboard?.pending_approvals_count ?? 0}
            </div>
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Pending Approvals
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
