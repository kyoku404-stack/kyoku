/**
 * Phase 3.3 Enterprise Security, Compliance & Governance Component Tests.
 *
 * Verifies UI components:
 * - SecurityMetricsBanner
 * - MFASetupModal
 * - AuditLogViewer
 * - DataClassificationDrawer
 * - ComplianceReportCard
 * - AIGovernanceInspector
 * - SecurityAlertsBanner
 * - RolePermissionMatrix
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import {
  SecurityMetricsBanner,
  MFASetupModal,
  AuditLogViewer,
  DataClassificationDrawer,
  ComplianceReportCard,
  AIGovernanceInspector,
  SecurityAlertsBanner,
  RolePermissionMatrix,
} from '@/features/security';
import {
  ClassificationLevel,
  SecurityAlertSeverity,
  SecurityAlertType,
} from '@/types/security';

describe('Phase 3.3 Security Feature Components', () => {
  it('SecurityMetricsBanner displays compliance score and active threat badges', () => {
    const mockCompliance = {
      overall_compliance_score: 96.5,
      standards: [],
    };
    const mockAlerts = [
      {
        id: 'alt-1',
        alert_type: SecurityAlertType.FAILED_LOGIN_SPIKE,
        severity: SecurityAlertSeverity.HIGH,
        description: 'Failed login spike from 10.0.0.1',
        source_ip: '10.0.0.1',
        resolved: false,
        triggered_at: '2026-10-28T10:00:00Z',
      },
    ];

    const onOpenMFA = vi.fn();
    const onRefresh = vi.fn();
    const onExport = vi.fn();

    render(
      <SecurityMetricsBanner
        compliance={mockCompliance}
        threatAlerts={mockAlerts}
        aiStats={{
          total_queries_audited: 120,
          guardrail_blocks: 4,
          avg_latency_ms: 15.2,
          prompt_injection_attempts: 2,
          safety_score_percentage: 97.5,
        }}
        mfaEnabled={false}
        onOpenMFAModal={onOpenMFA}
        onRefresh={onRefresh}
        onExportAudit={onExport}
        isLoading={false}
      />
    );

    expect(screen.getByText('Enterprise Security & Governance')).toBeInTheDocument();
    expect(screen.getByText('96.5%')).toBeInTheDocument();
    expect(screen.getByText('Requires Action')).toBeInTheDocument();
    expect(screen.getByText('Setup MFA')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Setup MFA'));
    expect(onOpenMFA).toHaveBeenCalled();
  });

  it('MFASetupModal renders 6-digit TOTP input and triggers verification', async () => {
    const onVerify = vi.fn().mockResolvedValue({});
    const onSetup = vi.fn();
    const onDisable = vi.fn();
    const onClose = vi.fn();

    render(
      <MFASetupModal
        isOpen={true}
        onClose={onClose}
        mfaSetup={{
          secret_key: 'TESTSECRETKEY123',
          otpauth_uri: 'otpauth://totp/KEEP',
          backup_codes: ['11112222', '33334444'],
        }}
        mfaEnabled={false}
        onSetupMFA={onSetup}
        onVerifyMFA={onVerify}
        onDisableMFA={onDisable}
        isLoading={false}
      />
    );

    expect(screen.getByText('Setup Multi-Factor Authentication')).toBeInTheDocument();
    expect(screen.getByDisplayValue('TESTSECRETKEY123')).toBeInTheDocument();

    const input = screen.getByPlaceholderText('123456');
    await act(async () => {
      fireEvent.change(input, { target: { value: '654321' } });
    });

    const verifyBtn = screen.getByRole('button', { name: /Verify & Activate MFA/i });
    await act(async () => {
      fireEvent.click(verifyBtn);
    });

    expect(onVerify).toHaveBeenCalledWith('654321');
  });

  it('AuditLogViewer renders log rows and handles action filtering', () => {
    const mockLogs = [
      {
        id: 'log-1',
        organization_id: 'org-1',
        action: 'MFA_ENABLED',
        resource: 'AUTH_CREDENTIAL',
        ip_address: '192.168.1.5',
        status: 'SUCCESS',
        details: { method: 'TOTP' },
        created_at: '2026-10-28T11:00:00Z',
      },
    ];

    const onFetch = vi.fn();
    const onExport = vi.fn();

    render(
      <AuditLogViewer
        logs={mockLogs}
        total={1}
        page={1}
        onFetchLogs={onFetch}
        onExport={onExport}
        isLoading={false}
      />
    );

    expect(screen.getByText('Immutable Audit Trail')).toBeInTheDocument();
    expect(screen.getByText('MFA_ENABLED')).toBeInTheDocument();
    expect(screen.getByText('SUCCESS')).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText('Filter by action...');
    fireEvent.change(searchInput, { target: { value: 'MFA' } });
    fireEvent.click(screen.getByText('Apply'));

    expect(onFetch).toHaveBeenCalledWith(
      expect.objectContaining({ action: 'MFA' })
    );
  });

  it('DataClassificationDrawer allows scanning content and renders classification tier', () => {
    const onClassify = vi.fn().mockResolvedValue({});
    const mockResult = {
      classification_level: ClassificationLevel.RESTRICTED,
      detected_pii_entities: [{ type: 'API_KEY', count: 1, masked_sample: 'ak_***' }],
      pii_count: 1,
      confidence_score: 0.99,
      redacted_preview: 'Super secret key: [REDACTED_API_KEY]',
    };

    render(
      <DataClassificationDrawer
        onClassify={onClassify}
        classificationResult={mockResult}
        isLoading={false}
      />
    );

    expect(screen.getByText('Sensitive Data Classification & PII Scanner')).toBeInTheDocument();
    expect(screen.getByText('RESTRICTED')).toBeInTheDocument();
    expect(screen.getByText(/API_KEY: 1/)).toBeInTheDocument();
    expect(screen.getByText('Super secret key: [REDACTED_API_KEY]')).toBeInTheDocument();
  });

  it('ComplianceReportCard renders standards scores and switches to retention tab', () => {
    const onSetRetention = vi.fn().mockResolvedValue({});
    const onErasure = vi.fn().mockResolvedValue({});

    render(
      <ComplianceReportCard
        compliance={{
          overall_compliance_score: 94.0,
          standards: [
            { standard: 'GDPR', score: 94.0, status: 'COMPLIANT', controls_passed: 18, controls_total: 20 },
            { standard: 'SOC_2', score: 95.0, status: 'COMPLIANT', controls_passed: 19, controls_total: 20 },
          ],
        }}
        onSetRetentionPolicy={onSetRetention}
        onExecuteErasure={onErasure}
        isLoading={false}
      />
    );

    expect(screen.getByText('Compliance Framework & Governance Engine')).toBeInTheDocument();
    expect(screen.getByText('GDPR')).toBeInTheDocument();
    expect(screen.getByText('SOC 2')).toBeInTheDocument();

    // Switch to retention rules tab
    fireEvent.click(screen.getByText('Retention Rules'));
    expect(screen.getByText('Resource Domain')).toBeInTheDocument();
    expect(screen.getByText('Apply Retention Policy')).toBeInTheDocument();
  });

  it('SecurityAlertsBanner displays active alerts and resolves on button click', () => {
    const onResolve = vi.fn().mockResolvedValue({});
    const alerts = [
      {
        id: 'alt-42',
        alert_type: 'PROMPT_INJECTION_ATTEMPT',
        severity: SecurityAlertSeverity.CRITICAL,
        description: 'Adversarial jailbreak payload blocked',
        source_ip: '45.33.32.156',
        resolved: false,
        triggered_at: '2026-10-28T12:00:00Z',
      },
    ];

    render(
      <SecurityAlertsBanner
        alerts={alerts}
        onResolveAlert={onResolve}
        isLoading={false}
      />
    );

    expect(screen.getByText(/Active Security Threat Incidents/)).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('Adversarial jailbreak payload blocked')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Resolve Incident'));
    expect(onResolve).toHaveBeenCalledWith('alt-42');
  });

  it('RolePermissionMatrix displays roles and toggles permissions', () => {
    const onUpdate = vi.fn().mockResolvedValue({});
    const matrix = [
      {
        role: 'SECURITY_OFFICER',
        description: 'Oversees enterprise security policies and telemetry',
        permissions: ['security:view', 'security:manage', 'data:classify'],
      },
      {
        role: 'AUDITOR',
        description: 'Audits access logs and compliance posture',
        permissions: ['security:view', 'security:audit'],
      },
    ];

    render(
      <RolePermissionMatrix
        rolesMatrix={matrix}
        onUpdateRolePermissions={onUpdate}
        isLoading={false}
      />
    );

    expect(screen.getByText('Role & Permission Access Matrix')).toBeInTheDocument();
    expect(screen.getByText('SECURITY_OFFICER')).toBeInTheDocument();
    expect(screen.getByText('AUDITOR')).toBeInTheDocument();

    // Toggle permission and save
    fireEvent.click(screen.getByText('Save Changes'));
    expect(onUpdate).toHaveBeenCalledWith(
      'SECURITY_OFFICER',
      expect.arrayContaining(['security:view', 'security:manage', 'data:classify'])
    );
  });

  it('AIGovernanceInspector displays safety stats and logs', () => {
    const onFetch = vi.fn();
    const logs = [
      {
        id: 'gov-1',
        prompt_snippet: 'Show customer SSN lists',
        model_name: 'gpt-4o',
        guardrail_status: 'BLOCKED',
        token_usage: 45,
        latency_ms: 12,
        created_at: '2026-10-28T12:00:00Z',
      },
    ];
    const stats = {
      total_queries_audited: 85,
      guardrail_blocks: 3,
      avg_latency_ms: 14.5,
      prompt_injection_attempts: 1,
      safety_score_percentage: 98.8,
    };

    render(
      <AIGovernanceInspector
        logs={logs}
        stats={stats}
        onFetchLogs={onFetch}
        isLoading={false}
      />
    );

    expect(screen.getByText('AI Governance & Prompt Injection Guardrails')).toBeInTheDocument();
    expect(screen.getByText('Show customer SSN lists')).toBeInTheDocument();
    expect(screen.getByText('BLOCKED')).toBeInTheDocument();
    expect(screen.getByText('12 ms')).toBeInTheDocument();
  });
});
