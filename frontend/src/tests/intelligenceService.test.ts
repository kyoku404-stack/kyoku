/**
 * KEEP Enterprise Platform — Enterprise Intelligence API Client Unit Tests (Phase 2.5).
 *
 * Verifies all 7 REST endpoints in intelligenceService:
 * - GET /api/v1/analytics/dashboard
 * - GET /api/v1/analytics/kpis
 * - GET /api/v1/analytics/trends
 * - GET /api/v1/analytics/predictions
 * - GET /api/v1/analytics/anomalies
 * - GET /api/v1/analytics/recommendations
 * - GET /api/v1/analytics/knowledge-health
 *
 * Specification: docs/api/api-contract.md Section 12 & devdocs/p2/p2.5.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { intelligenceService } from '@/services/intelligenceService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 2.5 Enterprise Intelligence Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getExecutiveDashboard() calls GET /analytics/dashboard', async () => {
    const mockData = {
      health_score: {
        overall_score: 88,
        rating: 'EXCELLENT',
        coverage_score: 92.0,
        freshness_score: 84.0,
        quality_score: 86.0,
        retrieval_score: 90.0,
        duplicate_penalty: 4.0,
        department_breakdown: [],
        identified_gaps: [],
      },
      kpis: {
        active_users: 42,
        documents_uploaded: 128,
        ai_queries: 450,
        search_success_rate: 0.94,
        avg_response_time_ms: 185.0,
        storage_used_bytes: 1073741824,
        storage_capacity_bytes: 10737418240,
        knowledge_health_score: 88,
      },
      active_anomalies_count: 1,
      top_recommendations_count: 3,
      executive_summary: 'Knowledge contributions increased by 18%.',
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockData },
    });

    const res = await intelligenceService.getExecutiveDashboard();

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/dashboard');
    expect(res.success).toBe(true);
    expect(res.data.health_score.overall_score).toBe(88);
    expect(res.data.kpis.active_users).toBe(42);
  });

  it('getKPIs() calls GET /analytics/kpis', async () => {
    const mockKPIs = {
      active_users: 25,
      documents_uploaded: 90,
      ai_queries: 310,
      search_success_rate: 0.92,
      avg_response_time_ms: 160.0,
      storage_used_bytes: 524288000,
      storage_capacity_bytes: 10737418240,
      knowledge_health_score: 82,
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockKPIs },
    });

    const res = await intelligenceService.getKPIs();

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/kpis');
    expect(res.success).toBe(true);
    expect(res.data.documents_uploaded).toBe(90);
  });

  it('getTrends() calls GET /analytics/trends with params', async () => {
    const mockTrends = {
      period_days: 60,
      document_growth: [{ date: '2026-10-01', value: 50 }],
      ai_query_volume: [{ date: '2026-10-01', value: 120 }],
      department_activity: [{ department: 'Engineering', document_count: 30, query_count: 100 }],
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockTrends },
    });

    const res = await intelligenceService.getTrends(60, 'documents');

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/trends', {
      params: { days: 60, metric: 'documents' },
    });
    expect(res.success).toBe(true);
    expect(res.data.period_days).toBe(60);
  });

  it('getPredictions() calls GET /analytics/predictions with horizon_days', async () => {
    const mockPredictions = {
      horizon_days: 90,
      document_forecast: {
        current_value: 120,
        projected_value: 175,
        growth_rate_pct: 45.8,
        confidence_lower: 160,
        confidence_upper: 190,
      },
      storage_runway: {
        current_usage_bytes: 1073741824,
        capacity_bytes: 10737418240,
        days_to_85_pct: 120,
        days_to_full: 155,
        is_critical: false,
      },
      query_volume_forecast: {
        current_daily_avg: 50.0,
        projected_daily_avg: 70.0,
        monthly_tokens_projected: 3000000,
      },
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockPredictions },
    });

    const res = await intelligenceService.getPredictions(90);

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/predictions', {
      params: { horizon_days: 90 },
    });
    expect(res.success).toBe(true);
    expect(res.data.storage_runway.days_to_85_pct).toBe(120);
  });

  it('getAnomalies() calls GET /analytics/anomalies', async () => {
    const mockAnomalies = {
      total_detected: 1,
      anomalies: [
        {
          id: 'anom-1',
          metric_name: 'login_burst',
          anomaly_type: 'UNUSUAL_LOGIN',
          severity: 'HIGH',
          description: '5 failed logins in 1 minute.',
          deviation_score: 2.8,
          detected_at: '2026-10-27T10:00:00Z',
        },
      ],
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockAnomalies },
    });

    const res = await intelligenceService.getAnomalies();

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/anomalies');
    expect(res.success).toBe(true);
    expect(res.data.total_detected).toBe(1);
    expect(res.data.anomalies[0].severity).toBe('HIGH');
  });

  it('getRecommendations() calls GET /analytics/recommendations with status', async () => {
    const mockRecs = {
      total_recommendations: 1,
      recommendations: [
        {
          id: 'rec-1',
          category: 'ARCHIVE',
          title: 'Archive Stale Docs',
          description: 'No views in 180 days.',
          impact_score: 8.0,
          effort_score: 2.0,
          priority_index: 6.0,
          status: 'ACTIVE',
        },
      ],
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockRecs },
    });

    const res = await intelligenceService.getRecommendations('ACTIVE');

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/recommendations', {
      params: { status: 'ACTIVE' },
    });
    expect(res.success).toBe(true);
    expect(res.data.recommendations[0].priority_index).toBe(6.0);
  });

  it('getKnowledgeHealth() calls GET /analytics/knowledge-health', async () => {
    const mockHealth = {
      overall_score: 91,
      rating: 'EXCELLENT',
      coverage_score: 95.0,
      freshness_score: 88.0,
      quality_score: 90.0,
      retrieval_score: 92.0,
      duplicate_penalty: 2.0,
      department_breakdown: [],
      identified_gaps: [],
    };

    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockHealth },
    });

    const res = await intelligenceService.getKnowledgeHealth();

    expect(apiClient.get).toHaveBeenCalledWith('/analytics/knowledge-health');
    expect(res.success).toBe(true);
    expect(res.data.overall_score).toBe(91);
    expect(res.data.rating).toBe('EXCELLENT');
  });
});
