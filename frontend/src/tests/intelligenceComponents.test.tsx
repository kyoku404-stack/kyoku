/**
 * Phase 2.5 Enterprise Intelligence & Predictive Analytics Components Unit Tests.
 *
 * Verifies UI components:
 * 1. KnowledgeHealthGauge
 * 2. ExecutiveBriefingCard
 * 3. ForecastVisualizer
 * 4. AnomalyAlertFeed
 * 5. RecommendationPanel
 * 6. TrendChartWidget
 *
 * Specification: docs/api/api-contract.md Section 12 & devdocs/p2/p2.5.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  KnowledgeHealthGauge,
  ExecutiveBriefingCard,
  ForecastVisualizer,
  AnomalyAlertFeed,
  RecommendationPanel,
  TrendChartWidget,
} from '@/features/intelligence';
import type {
  AnomaliesResponse,
  HealthScoreBreakdown,
  KPIsResponse,
  PredictionsResponse,
  RecommendationsResponse,
  TrendAnalysisResponse,
} from '@/types/intelligence';

describe('Phase 2.5 Intelligence UI Components', () => {
  it('KnowledgeHealthGauge renders score, rating badge, factor bars, and gaps', () => {
    const mockHealth: HealthScoreBreakdown = {
      overall_score: 85,
      rating: 'EXCELLENT',
      coverage_score: 90.0,
      freshness_score: 82.0,
      quality_score: 88.0,
      retrieval_score: 86.0,
      duplicate_penalty: 3.0,
      department_breakdown: [
        { department: 'Engineering', score: 92, rating: 'EXCELLENT', document_count: 50 },
      ],
      identified_gaps: ['HR documentation missing', 'Stale legal guidelines'],
    };

    render(<KnowledgeHealthGauge health={mockHealth} />);

    expect(screen.getByTestId('knowledge-health-gauge')).toBeInTheDocument();
    expect(screen.getByTestId('khs-score-value')).toHaveTextContent('85');
    expect(screen.getAllByText('EXCELLENT').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Coverage Factor (30% weight)')).toBeInTheDocument();
    expect(screen.getByText('HR documentation missing')).toBeInTheDocument();
    expect(screen.getByText('Engineering')).toBeInTheDocument();
  });

  it('ExecutiveBriefingCard renders summary narrative and KPI cards', () => {
    const mockKPIs: KPIsResponse = {
      active_users: 38,
      documents_uploaded: 115,
      ai_queries: 420,
      search_success_rate: 0.95,
      avg_response_time_ms: 180.0,
      storage_used_bytes: 104857600,
      storage_capacity_bytes: 10737418240,
      knowledge_health_score: 85,
    };

    render(
      <ExecutiveBriefingCard
        summary="Knowledge contributions increased by 22% with strong AI adoption."
        kpis={mockKPIs}
      />
    );

    expect(screen.getByTestId('executive-briefing-card')).toBeInTheDocument();
    expect(screen.getByTestId('executive-briefing-text')).toHaveTextContent(
      'Knowledge contributions increased by 22% with strong AI adoption.'
    );
    expect(screen.getByText('38')).toBeInTheDocument();
    expect(screen.getByText('115 docs')).toBeInTheDocument();
    expect(screen.getByText('420')).toBeInTheDocument();
  });

  it('ForecastVisualizer renders document projection, tokens, and storage runway', () => {
    const mockPredictions: PredictionsResponse = {
      horizon_days: 30,
      document_forecast: {
        current_value: 115,
        projected_value: 150,
        growth_rate_pct: 30.4,
        confidence_lower: 140,
        confidence_upper: 160,
      },
      storage_runway: {
        current_usage_bytes: 104857600,
        capacity_bytes: 10737418240,
        days_to_85_pct: 180,
        days_to_full: 220,
        is_critical: false,
      },
      query_volume_forecast: {
        current_daily_avg: 40.0,
        projected_daily_avg: 55.0,
        monthly_tokens_projected: 2200000,
      },
    };

    const horizonSpy = vi.fn();

    render(
      <ForecastVisualizer
        predictions={mockPredictions}
        horizonDays={30}
        onHorizonChange={horizonSpy}
      />
    );

    expect(screen.getByTestId('forecast-visualizer')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('+30.4%')).toBeInTheDocument();
    expect(screen.getByText('180')).toBeInTheDocument();
    expect(screen.getByText('2.20M Tokens')).toBeInTheDocument();

    const btn60d = screen.getByText('60d');
    fireEvent.click(btn60d);
    expect(horizonSpy).toHaveBeenCalledWith(60);
  });

  it('AnomalyAlertFeed renders detected anomalies and filters by severity', () => {
    const mockAnomalies: AnomaliesResponse = {
      total_detected: 2,
      anomalies: [
        {
          id: 'anom-1',
          metric_name: 'api_failure_spike',
          anomaly_type: 'API_FAILURE_SPIKE',
          severity: 'CRITICAL',
          description: 'Error rate increased 3.5x.',
          deviation_score: 3.4,
          detected_at: '2026-10-27T12:00:00Z',
        },
        {
          id: 'anom-2',
          metric_name: 'login_drop',
          anomaly_type: 'ACTIVITY_DROP',
          severity: 'LOW',
          description: 'Slightly fewer logins on Sunday.',
          deviation_score: 1.8,
          detected_at: '2026-10-27T14:00:00Z',
        },
      ],
    };

    render(<AnomalyAlertFeed anomaliesData={mockAnomalies} />);

    expect(screen.getByTestId('anomaly-alert-feed')).toBeInTheDocument();
    expect(screen.getByText('api failure spike')).toBeInTheDocument();
    expect(screen.getAllByText('CRITICAL').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/3\.40/)).toBeInTheDocument();

    // Filter to LOW
    const lowFilter = screen.getByRole('button', { name: 'LOW' });
    fireEvent.click(lowFilter);
    expect(screen.queryByText('api failure spike')).not.toBeInTheDocument();
    expect(screen.getByText('login drop')).toBeInTheDocument();
  });

  it('RecommendationPanel renders recommendations with Priority Index and handles apply', () => {
    const mockRecs: RecommendationsResponse = {
      total_recommendations: 1,
      recommendations: [
        {
          id: 'rec-1',
          category: 'ARCHIVE',
          title: 'Archive 10 Stale Specs',
          description: 'No views in 180 days.',
          impact_score: 7.0,
          effort_score: 1.5,
          priority_index: 7.0,
          status: 'ACTIVE',
        },
      ],
    };

    render(<RecommendationPanel recommendationsData={mockRecs} />);

    expect(screen.getByTestId('recommendation-panel')).toBeInTheDocument();
    expect(screen.getByText('Archive 10 Stale Specs')).toBeInTheDocument();
    expect(screen.getByText('PI: 7.0')).toBeInTheDocument();

    const executeBtn = screen.getByText('Execute');
    fireEvent.click(executeBtn);
    expect(screen.getByText('Applied')).toBeInTheDocument();
  });

  it('TrendChartWidget renders multi-series curves and department bars', () => {
    const mockTrends: TrendAnalysisResponse = {
      period_days: 30,
      document_growth: [
        { date: '2026-10-01', value: 40 },
        { date: '2026-10-15', value: 65 },
      ],
      ai_query_volume: [
        { date: '2026-10-01', value: 120 },
        { date: '2026-10-15', value: 210 },
      ],
      department_activity: [
        { department: 'Engineering', document_count: 45, query_count: 180 },
      ],
    };

    const periodSpy = vi.fn();

    render(
      <TrendChartWidget
        trends={mockTrends}
        periodDays={30}
        onPeriodChange={periodSpy}
      />
    );

    expect(screen.getByTestId('trend-chart-widget')).toBeInTheDocument();
    expect(screen.getByText('Document Upload Growth')).toBeInTheDocument();
    expect(screen.getByText('AI Queries & Search Volume')).toBeInTheDocument();
    expect(screen.getByText('Engineering')).toBeInTheDocument();

    const btn60d = screen.getByText('60d');
    fireEvent.click(btn60d);
    expect(periodSpy).toHaveBeenCalledWith(60);
  });
});
