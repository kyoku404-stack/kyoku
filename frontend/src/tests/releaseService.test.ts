/**
 * Phase 3.7 Production Release & Security Audit API Client Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { releaseService } from '@/services/releaseService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 3.7 Release Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getReadiness() queries /api/v1/system/readiness with target_version', async () => {
    const mockReadiness = {
      is_ready: true,
      overall_score: 1.0,
      evaluated_at: '2026-11-06T05:00:00Z',
      target_version: '1.0.0',
      git_commit: '8767c08',
      checks: [
        {
          check_name: 'database_migrations',
          category: 'PERSISTENCE',
          status: 'PASSED',
          score: 1.0,
          details: {},
          verified_at: '2026-11-06T05:00:00Z',
        },
      ],
      failing_checks: [],
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Ready', data: mockReadiness },
    });

    const res = await releaseService.getReadiness('1.0.0');
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/readiness', {
      params: { target_version: '1.0.0' },
    });
    expect(res.data.is_ready).toBe(true);
    expect(res.data.overall_score).toBe(1.0);
    expect(res.data.checks).toHaveLength(1);
  });

  it('triggerRelease() posts to /api/v1/system/release with deployment spec', async () => {
    const requestPayload = {
      version: '1.0.0',
      release_tag: 'v1.0.0',
      changelog: 'Production release for Phase 3.7',
      environment: 'production',
      enforce_preflight: true,
    };

    const mockDeployData = {
      release_id: 'rel-v1.0.0-abc',
      version: '1.0.0',
      release_tag: 'v1.0.0',
      git_commit: '8767c08',
      status: 'COMPLETED',
      preflight_score: 1.0,
      deployed_by: 'user-admin',
      started_at: '2026-11-06T05:00:00Z',
      completed_at: '2026-11-06T05:00:05Z',
      changelog: 'Production release for Phase 3.7',
      artifacts: { manifest_checksum_sha256: 'abcdef123456' },
    };

    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Deployed', data: mockDeployData },
    });

    const res = await releaseService.triggerRelease(requestPayload);
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/system/release', requestPayload);
    expect(res.data.status).toBe('COMPLETED');
    expect(res.data.release_tag).toBe('v1.0.0');
  });

  it('getReleaseHistory() queries /api/v1/system/releases with limit', async () => {
    const mockReleases = [
      {
        release_id: 'rel-1',
        version: '1.0.0',
        release_tag: 'v1.0.0',
        git_commit: '8767c08',
        status: 'COMPLETED',
        preflight_score: 1.0,
        deployed_by: 'user-1',
        created_at: '2026-11-06T05:00:00Z',
        completed_at: '2026-11-06T05:00:05Z',
      },
    ];

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockReleases },
    });

    const res = await releaseService.getReleaseHistory(10);
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/releases', {
      params: { limit: 10 },
    });
    expect(res.data).toHaveLength(1);
    expect(res.data[0].version).toBe('1.0.0');
  });

  it('getSecurityAudit() queries /api/v1/system/security/audit', async () => {
    const mockAudit = {
      compliance_standard: 'OWASP_TOP_10_AND_LLM_TOP_10',
      overall_compliance_percent: 100.0,
      evaluated_at: '2026-11-06T05:00:00Z',
      total_controls: 10,
      passed_controls: 10,
      failed_controls: 0,
      controls: [
        {
          control_id: 'SEC-01',
          name: 'SQL Injection Defense',
          status: 'PASSED',
          severity: 'CRITICAL',
          description: 'SQLAlchemy 2.0 ORM parameterization enforced.',
          mitigation: 'Ban raw queries.',
        },
      ],
      findings: [],
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, message: 'Audit Passed', data: mockAudit },
    });

    const res = await releaseService.getSecurityAudit();
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/system/security/audit');
    expect(res.data.overall_compliance_percent).toBe(100.0);
    expect(res.data.passed_controls).toBe(10);
  });
});
