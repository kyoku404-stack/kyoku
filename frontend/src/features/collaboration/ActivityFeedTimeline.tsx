/**
 * Phase 3.2 ActivityFeedTimeline Component.
 * Vertical chronological timeline of workspace activities with filter tabs.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  MessageSquare,
  FileUp,
  UserPlus,
  Sparkles,
  GitCommit,
  CheckCircle,
  Clock,
  Layers,
} from 'lucide-react';
import type { ActivityItem } from '@/types/collaboration';

interface ActivityFeedTimelineProps {
  activities: ActivityItem[];
  workspaceName?: string;
  onClose?: () => void;
}

export const ActivityFeedTimeline: React.FC<ActivityFeedTimelineProps> = ({
  activities,
  workspaceName,
  onClose,
}) => {
  const [filter, setFilter] = useState<string>('ALL');

  const filtered = activities.filter((a) => {
    if (filter === 'ALL') return true;
    return a.activity_type === filter;
  });

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'COMMENT_ADDED':
      case 'REPLY_ADDED':
        return <MessageSquare className="w-4 h-4 text-indigo-500" />;
      case 'DOCUMENT_UPLOAD':
      case 'DOCUMENT_UPDATE':
        return <FileUp className="w-4 h-4 text-emerald-500" />;
      case 'MEMBER_JOINED':
        return <UserPlus className="w-4 h-4 text-blue-500" />;
      case 'AI_SUMMARY_GENERATED':
        return <Sparkles className="w-4 h-4 text-purple-500" />;
      case 'DISCUSSION_RESOLVED':
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case 'VERSION_CHECKPOINT':
        return <GitCommit className="w-4 h-4 text-amber-500" />;
      default:
        return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="flex flex-col gap-4 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm">
      {/* Header & Filter Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-500" />
            Activity Timeline {workspaceName && `· ${workspaceName}`}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time audit log of team actions and knowledge updates
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {['ALL', 'COMMENT_ADDED', 'DOCUMENT_UPLOAD', 'MEMBER_JOINED', 'AI_SUMMARY_GENERATED'].map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg transition-all ${
                filter === t
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
              }`}
            >
              {t === 'ALL'
                ? 'All'
                : t === 'COMMENT_ADDED'
                  ? 'Comments'
                  : t === 'DOCUMENT_UPLOAD'
                    ? 'Uploads'
                    : t === 'MEMBER_JOINED'
                      ? 'Members'
                      : 'AI'}
            </button>
          ))}
          {onClose && (
            <button
              onClick={onClose}
              className="text-xs text-slate-400 hover:text-slate-600 px-2 py-1"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Timeline items */}
      {filtered.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400">
          No activity records found matching this filter.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
          {filtered.map((act) => (
            <div key={act.id} className="relative flex items-start gap-3 group">
              {/* Timeline Pip */}
              <div className="absolute -left-6 mt-0.5 w-5 h-5 rounded-full bg-white dark:bg-slate-900 border-2 border-indigo-500 flex items-center justify-center ring-4 ring-white dark:ring-slate-900">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              </div>

              {/* Content Card */}
              <div className="flex-1 p-3 rounded-xl bg-slate-50/70 dark:bg-slate-950/70 border border-slate-100 dark:border-slate-800/60 hover:border-slate-200 dark:hover:border-slate-700 transition-colors">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5">
                    {getActivityIcon(act.activity_type)}
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      {act.actor_name}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(act.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {act.description}
                </p>
                {act.entity_title && (
                  <div className="mt-1.5 text-[11px] font-medium text-indigo-600 dark:text-indigo-400">
                    Ref: {act.entity_title}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
