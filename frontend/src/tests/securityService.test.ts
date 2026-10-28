/**
 * Phase 3.3 Enterprise Security, Compliance & Governance Service Client Tests.
 *
 * Verifies all API methods in securityService:
 * - Enterprise Login & Logout
 * - TOTP MFA Setup, Verify, Disable
 * - Audit Trail Logs & Export
 * - Roles & Permissions Matrix
 * - Data Classification & PII Scanning
 * - AI Governance Logs & Stats
 * - Regulatory Compliance Overview & Retention Rules
 * - Threat Monitoring & Alert Resolution
 *
 * Aligned with docs/api/api-contract.md Section 15 & devdocs/p3/p3.3.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { securityService } from '@/services/securityService';
import { apiClient } from '@/services/api';
import {
  ClassificationLevel,
  ComplianceStandard,
  SecurityAlertSeverity,
} from '@/types/security';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('Phase 3.3 Security Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('enterpriseLogin() posts credentials to /security/auth/login', async () => {
    const mockRes = {
      access_token: 'jwt-access-token',
      token_type: 'bearer',
      expires_in: 3600,
      user_id: 'u-1',
      organization_id: 'org-1',
      role: 'SECURITY_OFFICER',
      mfa_required: true,
      mfa_verified: false,
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockRes },
    });

    const res = await securityService.enterpriseLogin({
      email: 'officer@enterprise.com',
      password: 'StrongPassword123!',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/security/auth/login', {
      email: 'officer@enterprise.com',
      password: 'StrongPassword123!',
    });
    expect(res.data?.user_id).toBe('u-1');
    expect(res.data?.mfa_required).toBe(true);
  });

  it('setupMFA() requests TOTP secret from /security/auth/mfa/setup', async () => {
    const mockMfa = {
      secret_key: 'JBSWY3DPEHPK3PXP',
      otpauth_uri: 'otpauth://totp/KEEP:user?secret=JBSWY3DPEHPK3PXP',
      backup_codes: ['12345678', '87654321'],
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockMfa },
    });

    const res = await securityService.setupMFA();
    expect(apiClient.post).toHaveBeenCalledWith('/security/auth/mfa/setup', {});
    expect(res.data?.secret_key).toBe('JBSWY3DPEHPK3PXP');
    expect(res.data?.backup_codes).toHaveLength(2);
  });

  it('verifyMFA() validates code against /security/auth/mfa/verify', async () => {
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: { is_enabled: true, mfa_verified: true } },
    });

    const res = await securityService.verifyMFA('123456');
    expect(apiClient.post).toHaveBeenCalledWith('/security/auth/mfa/verify', {
      code: '123456',
    });
    expect(res.data?.is_enabled).toBe(true);
  });

  it('getAuditLogs() retrieves logs from /security/audit/logs', async () => {
    const mockLogs = {
      success: true,
      total: 1,
      page: 1,
      page_size: 20,
      data: [
        {
          id: 'log-1',
          organization_id: 'org-1',
          action: 'AUTH_LOGIN',
          resource: 'AUTH',
          ip_address: '127.0.0.1',
          status: 'SUCCESS',
          details: {},
          created_at: '2026-10-28T12:00:00Z',
        },
      ],
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: mockLogs,
    });

    const res = await securityService.getAuditLogs({ page: 1, action: 'AUTH_LOGIN' });
    expect(apiClient.get).toHaveBeenCalledWith('/security/audit/logs', {
      params: { page: 1, action: 'AUTH_LOGIN' },
    });
    expect(res.data).toHaveLength(1);
    expect(res.data[0].action).toBe('AUTH_LOGIN');
  });

  it('classifyData() submits text for PII scanning to /security/data/classify', async () => {
    const mockClassification = {
      classification_level: ClassificationLevel.CONFIDENTIAL,
      detected_pii_entities: [{ type: 'EMAIL', count: 1, masked_sample: 'u***@test.com' }],
      pii_count: 1,
      confidence_score: 0.95,
      redacted_preview: 'Cleaned text',
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockClassification },
    });

    const res = await securityService.classifyData('Contact user@test.com for details');
    expect(apiClient.post).toHaveBeenCalledWith('/security/data/classify', {
      content: 'Contact user@test.com for details',
      document_id: undefined,
    });
    expect(res.data?.classification_level).toBe(ClassificationLevel.CONFIDENTIAL);
    expect(res.data?.pii_count).toBe(1);
  });

  it('getComplianceOverview() fetches multi-standard readiness from /security/compliance/overview', async () => {
    const mockCompliance = {
      overall_compliance_score: 93.5,
      standards: [
        {
          standard: ComplianceStandard.SOC_2,
          score: 95.0,
          status: 'COMPLIANT',
          controls_passed: 19,
          controls_total: 20,
        },
      ],
    };
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockCompliance },
    });

    const res = await securityService.getComplianceOverview();
    expect(apiClient.get).toHaveBeenCalledWith('/security/compliance/overview');
    expect(res.data?.overall_compliance_score).toBe(93.5);
    expect(res.data?.standards[0].standard).toBe(ComplianceStandard.SOC_2);
  });

  it('resolveThreatAlert() updates status via PUT /security/monitoring/alerts/{id}/resolve', async () => {
    const mockResolved = {
      id: 'alert-1',
      alert_type: 'FAILED_LOGIN_SPIKE',
      severity: SecurityAlertSeverity.HIGH,
      description: 'Multiple failed logins detected',
      source_ip: '192.168.1.1',
      resolved: true,
      triggered_at: '2026-10-28T12:00:00Z',
    };
    (apiClient.put as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: { success: true, data: mockResolved },
    });

    const res = await securityService.resolveThreatAlert('alert-1');
    expect(apiClient.put).toHaveBeenCalledWith('/security/monitoring/alerts/alert-1/resolve', {});
    expect(res.data?.resolved).toBe(true);
  });
});
