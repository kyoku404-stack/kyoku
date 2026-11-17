/**
 * KEEP Enterprise Platform — Phase 4.2 Runtime Observability KPI Banner.
 *
 * Displays live execution throughput, active concurrency, success rate, average duration,
 * timeout/cancellation counts, and retry telemetry from `/api/v1/executions/metrics`.
 */

import React from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  RefreshCcw,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import type { RuntimeMetricsData } from '@/types/agentRuntime';

interface RuntimeMetricsBannerProps {
  metrics: RuntimeMetricsData | null;
  loading?: boolean;
}

export const RuntimeMetricsBanner: React.FC<RuntimeMetricsBannerProps> = ({
  metrics,
  loading = false,
}) => {
  const cards = [
    {
      label: 'Completed Runs',
      value: metrics ? String(metrics.total_completed) : '0',
      subtext: metrics ? `p95: ${Math.round(metrics.p95_duration_ms)} ms` : 'Awaiting runs',
      icon: CheckCircle2,
      iconBg: 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    },
    {
      label: 'Active Executions',
      value: metrics ? String(metrics.active_executions) : '0',
      subtext: metrics ? `Queue wait: ${Math.round(metrics.avg_queue_wait_ms)} ms` : 'Idle',
      icon: Activity,
      iconBg: 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
    },
    {
      label: 'Success Rate',
      value: metrics ? `${metrics.success_rate_percent.toFixed(1)}%` : '100.0%',
      subtext: metrics
        ? `${metrics.output_validation_failures} schema validation failures`
        : 'Validated outputs',
      icon: Zap,
      iconBg: 'bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400',
    },
    {
      label: 'Avg Duration',
      value: metrics ? `${Math.round(metrics.avg_duration_ms)} ms` : '0 ms',
      subtext: 'Bounded execution SLA',
      icon: Clock,
      iconBg: 'bg-sky-50 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400',
    },
    {
      label: 'Timeouts / Cancelled',
      value: metrics ? `${metrics.timeout_count} / ${metrics.cancellation_count}` : '0 / 0',
      subtext: 'Safety & cooperative stops',
      icon: ShieldAlert,
      iconBg: 'bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    },
    {
      label: 'Retries Scheduled',
      value: metrics ? String(metrics.retry_count) : '0',
      subtext: 'Bounded transient retries',
      icon: RefreshCcw,
      iconBg: 'bg-teal-50 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400',
    },
  ];

  return (
    <section aria-label="Runtime Observability Metrics">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 shadow-xs flex flex-col justify-between"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                {card.label}
              </span>
              <span className={`p-1.5 rounded-lg ${card.iconBg}`}>
                <card.icon className="w-4 h-4" />
              </span>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {loading && !metrics ? '—' : card.value}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                {card.subtext}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
