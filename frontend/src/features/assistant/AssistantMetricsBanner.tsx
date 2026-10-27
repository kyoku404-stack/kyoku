import React from 'react';
import { PlayCircle, ShieldAlert, Zap, FileSpreadsheet, Activity } from 'lucide-react';
import type { AssistantMetrics } from '@/types/assistant';

interface AssistantMetricsBannerProps {
  metrics: AssistantMetrics;
  onRefresh?: () => void;
}

export const AssistantMetricsBanner: React.FC<AssistantMetricsBannerProps> = ({
  metrics,
  onRefresh,
}) => {
  const cards = [
    {
      title: 'Active Workflows',
      value: metrics.active_workflows,
      subtext: 'In execution / scheduled',
      icon: PlayCircle,
      accentColor: 'text-indigo-400',
      bgGlow: 'bg-indigo-500/10 border-indigo-500/20',
    },
    {
      title: 'Pending Approvals',
      value: metrics.pending_approvals,
      subtext: 'Requires human confirmation',
      icon: ShieldAlert,
      accentColor: metrics.pending_approvals > 0 ? 'text-amber-400' : 'text-emerald-400',
      bgGlow:
        metrics.pending_approvals > 0
          ? 'bg-amber-500/10 border-amber-500/30'
          : 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      title: 'Automated Tasks',
      value: metrics.tasks_automated,
      subtext: 'Tools executed autonomously',
      icon: Zap,
      accentColor: 'text-emerald-400',
      bgGlow: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      title: 'Reports Generated',
      value: metrics.reports_generated,
      subtext: 'Meeting & weekly briefings',
      icon: FileSpreadsheet,
      accentColor: 'text-sky-400',
      bgGlow: 'bg-sky-500/10 border-sky-500/20',
    },
  ];

  return (
    <div className="w-full mb-6">
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <h2 className="text-xs font-semibold tracking-wider uppercase text-slate-400">
            Assistant Platform Telemetry
          </h2>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            Refresh Metrics
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border backdrop-blur-md transition-all duration-200 hover:shadow-lg ${card.bgGlow}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-400">{card.title}</span>
                <Icon className={`w-5 h-5 ${card.accentColor}`} />
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">{card.value}</div>
              <p className="text-[11px] text-slate-400 mt-1">{card.subtext}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
