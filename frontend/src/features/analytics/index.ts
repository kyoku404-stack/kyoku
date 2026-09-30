/**
 * Analytics & Observability Feature Module
 * System metrics, query performance, storage tracking, and telemetry.
 */

export * from '@/types/analytics';
export { analyticsService } from '@/services/analyticsService';

export const ANALYTICS_FEATURE = {
  name: 'analytics',
  version: '1.2.0',
  description: 'Enterprise operational intelligence, token usage, and telemetry dashboards',
};
