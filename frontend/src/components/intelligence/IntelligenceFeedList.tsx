import React from 'react';
import type { InsightCategory, InsightStatus, IntelligenceInsight } from '@/types/proactiveIntelligence';

interface Props {
  insights: IntelligenceInsight[];
  selectedId?: string;
  categoryFilter: InsightCategory | 'all';
  statusFilter: InsightStatus;
  loading: boolean;
  onSelect: (insightId: string) => void;
  onCategoryChange: (category: InsightCategory | 'all') => void;
  onStatusChange: (status: InsightStatus) => void;
}

const CATEGORY_LABELS: Record<InsightCategory, string> = {
  significant_change: 'Significant Change',
  contradiction: 'Contradiction',
  stale_knowledge: 'Stale Knowledge',
  knowledge_gap: 'Knowledge Gap',
  emerging_trend: 'Emerging Trend',
};

export const IntelligenceFeedList: React.FC<Props> = ({
  insights,
  selectedId,
  categoryFilter,
  statusFilter,
  loading,
  onSelect,
  onCategoryChange,
  onStatusChange,
}) => {
  return (
    <section
      aria-label="Intelligence feed list"
      className="flex flex-col rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 p-3 dark:border-slate-700">
        <select
          aria-label="Filter by category"
          value={categoryFilter}
          onChange={(e) => onCategoryChange(e.target.value as InsightCategory | 'all')}
          className="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          <option value="all">All Categories</option>
          <option value="significant_change">Significant Change</option>
          <option value="contradiction">Contradiction</option>
          <option value="stale_knowledge">Stale Knowledge</option>
          <option value="knowledge_gap">Knowledge Gap</option>
          <option value="emerging_trend">Emerging Trend</option>
        </select>

        <select
          aria-label="Filter by status"
          value={statusFilter}
          onChange={(e) => onStatusChange(e.target.value as InsightStatus)}
          className="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          <option value="published">Published</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>

      {loading && insights.length === 0 ? (
        <p className="p-4 text-sm text-slate-500">Loading proactive insights...</p>
      ) : insights.length === 0 ? (
        <p className="p-4 text-sm text-slate-500">No insights match the selected filter.</p>
      ) : (
        <ul role="list" className="divide-y divide-slate-200 dark:divide-slate-700">
          {insights.map((ins) => {
            const isSelected = ins.insight_id === selectedId;
            return (
              <li key={ins.insight_id}>
                <button
                  type="button"
                  onClick={() => onSelect(ins.insight_id)}
                  aria-current={isSelected ? 'true' : undefined}
                  className={`w-full p-3.5 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50 ${
                    isSelected ? 'bg-indigo-50/80 dark:bg-indigo-950/40' : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="inline-flex items-center rounded bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                      {CATEGORY_LABELS[ins.category]}
                    </span>
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Score {ins.priority_score.toFixed(1)}
                    </span>
                  </div>
                  <h3 className="mt-1.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {ins.title}
                  </h3>
                  <p className="mt-1 line-clamp-2 text-xs text-slate-600 dark:text-slate-400">
                    {ins.summary}
                  </p>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
};
