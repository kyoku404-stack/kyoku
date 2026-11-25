import React from 'react';
import type { OperationalMetrics } from '@/types/proactiveIntelligence';

interface Props {
  metrics: OperationalMetrics | null;
}

export const IntelligenceMetricsBar: React.FC<Props> = ({ metrics }) => {
  const cards = [
    { label: 'Published Insights', value: metrics?.published_insights ?? 0 },
    { label: 'Suppressed Duplicates', value: metrics?.suppressed_insights ?? 0 },
    {
      label: 'Suppression Rate',
      value: `${Math.round((metrics?.duplicate_suppression_rate ?? 0) * 100)}%`,
    },
    { label: 'Detection Runs', value: metrics?.total_runs ?? 0 },
  ];

  return (
    <section
      aria-label="Proactive intelligence metrics"
      className="grid grid-cols-2 gap-3 sm:grid-cols-4"
    >
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-800"
        >
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{card.label}</p>
          <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">
            {card.value}
          </p>
        </div>
      ))}
    </section>
  );
};
