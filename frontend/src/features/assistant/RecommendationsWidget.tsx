import React from 'react';
import { Lightbulb, BookmarkCheck, FileWarning, Copy, FolderArchive, X } from 'lucide-react';
import type { ProactiveRecommendationItem, RecommendationCategory } from '@/types/assistant';

interface RecommendationsWidgetProps {
  recommendations: ProactiveRecommendationItem[];
  onDismiss: (id: string) => void;
  onApplyAction?: (rec: ProactiveRecommendationItem) => void;
}

export const RecommendationsWidget: React.FC<RecommendationsWidgetProps> = ({
  recommendations,
  onDismiss,
  onApplyAction,
}) => {
  const getCategoryIcon = (category: RecommendationCategory) => {
    switch (category) {
      case 'FREQUENT_DOCUMENTS':
        return <BookmarkCheck className="w-4 h-4 text-emerald-400" />;
      case 'MISSING_DOCUMENTATION':
        return <FileWarning className="w-4 h-4 text-amber-400" />;
      case 'DUPLICATE_KNOWLEDGE':
        return <Copy className="w-4 h-4 text-sky-400" />;
      case 'INACTIVE_PROJECTS':
        return <FolderArchive className="w-4 h-4 text-purple-400" />;
      default:
        return <Lightbulb className="w-4 h-4 text-indigo-400" />;
    }
  };

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 backdrop-blur-md mb-6">
      <div className="flex items-center space-x-2 mb-3">
        <Lightbulb className="w-4 h-4 text-amber-400" />
        <h3 className="text-xs font-bold tracking-wider uppercase text-slate-300">
          Proactive AI Recommendations
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex items-start justify-between group hover:border-slate-700 transition-colors"
          >
            <div className="flex items-start space-x-2.5">
              <div className="mt-0.5">{getCategoryIcon(rec.category)}</div>
              <div>
                <h4 className="text-xs font-semibold text-slate-200">{rec.title}</h4>
                <p className="text-[11px] text-slate-400 mt-0.5 leading-normal">{rec.description}</p>
                <div className="mt-2 flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => onApplyAction?.(rec)}
                    className="text-[10px] font-semibold text-indigo-400 hover:text-indigo-300 underline"
                  >
                    Action: {rec.suggested_action}
                  </button>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onDismiss(rec.id)}
              className="text-slate-500 hover:text-slate-300 p-1 rounded transition-colors opacity-70 group-hover:opacity-100"
              title="Dismiss recommendation"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
