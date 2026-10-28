/**
 * Custom React hook for Enterprise Security, Compliance, Governance & Data Protection.
 * Manages MFA setup/verification, audit trail logs & export, role-permission matrix,
 * data classification scans, AI safety telemetry, compliance scoring, and threat alerts.
 *
 * Aligned with docs/api/api-contract.md Section 15 & devdocs/p3/p3.3.txt
 * Author: Member 3 (Frontend & UI Lead)
 */

import { useCallback, useEffect, useState } from 'react';
import { securityService, type AuditLogQueryParams, type AIGovernanceQueryParams, type SecurityAlertQueryParams } from '@/services/securityService';
import type {
  AIGovernanceLogItem,
  AIGovernanceStatsData,
  ComplianceOverviewData,
  DataClassificationScanData,
  DataRetentionPolicyPayload,
  DataRetentionRuleData,
  GDPRErasureData,
  GDPRErasurePayload,
  MFASetupData,
  MFAVerifyData,
  RolePermissionItem,
  SecurityAuditLogItem,
  SecurityThreatAlertItem,
} from '@/types/security';

export function useSecurity() {
  const [compliance, setCompliance] = useState<ComplianceOverviewData | null>(null);
  const [auditLogs, setAuditLogs] = useState<SecurityAuditLogItem[]>([]);
  const [auditTotal, setAuditTotal] = useState<number>(0);
  const [auditPage, setAuditPage] = useState<number>(1);
  const [rolesMatrix, setRolesMatrix] = useState<RolePermissionItem[]>([]);
  const [mfaSetup, setMfaSetup] = useState<MFASetupData | null>(null);
  const [mfaStatus, setMfaStatus] = useState<MFAVerifyData | null>(null);
  const [classificationResult, setClassificationResult] = useState<DataClassificationScanData | null>(null);
  const [aiGovernanceLogs, setAiGovernanceLogs] = useState<AIGovernanceLogItem[]>([]);
  const [aiGovernanceStats, setAiGovernanceStats] = useState<AIGovernanceStatsData | null>(null);
  const [threatAlerts, setThreatAlerts] = useState<SecurityThreatAlertItem[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ==========================================================================
  // Compliance
  // ==========================================================================
  const fetchCompliance = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.getComplianceOverview();
      if (res.data) {
        setCompliance(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch compliance overview';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Audit Logs
  // ==========================================================================
  const fetchAuditLogs = useCallback(async (params?: AuditLogQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.getAuditLogs(params);
      if (res && res.data) {
        setAuditLogs(res.data);
        setAuditTotal(res.total || res.data.length);
        setAuditPage(res.page || 1);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch audit logs';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const exportAuditLogs = useCallback(async (format: 'json' | 'csv' = 'json') => {
    try {
      setLoading(true);
      const blob = await securityService.exportAuditLogs(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to export audit logs';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Roles Matrix
  // ==========================================================================
  const fetchRolesMatrix = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.getRolesMatrix();
      if (res.data) {
        setRolesMatrix(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch roles matrix';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateRolePermissions = useCallback(async (role: string, permissions: string[]) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.updateRolePermissions(role, permissions);
      if (res.data) {
        setRolesMatrix((prev) =>
          prev.map((item) => (item.role === role ? res.data! : item))
        );
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : `Failed to update permissions for role ${role}`;
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Multi-Factor Authentication
  // ==========================================================================
  const setupMFA = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.setupMFA();
      if (res.data) {
        setMfaSetup(res.data);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to initiate MFA setup';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyMFA = useCallback(async (code: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.verifyMFA(code);
      if (res.data) {
        setMfaStatus(res.data);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to verify MFA code';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const disableMFA = useCallback(async (code: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.disableMFA(code);
      setMfaSetup(null);
      setMfaStatus(null);
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to disable MFA';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Data Classification & PII Scanner
  // ==========================================================================
  const classifyContent = useCallback(async (content: string, documentId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.classifyData(content, documentId);
      if (res.data) {
        setClassificationResult(res.data);
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to classify data';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // AI Governance
  // ==========================================================================
  const fetchAIGovernance = useCallback(async (params?: AIGovernanceQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const [logsRes, statsRes] = await Promise.all([
        securityService.getAIGovernanceLogs(params),
        securityService.getAIGovernanceStats(),
      ]);
      if (logsRes && logsRes.data) {
        setAiGovernanceLogs(logsRes.data);
      }
      if (statsRes && statsRes.data) {
        setAiGovernanceStats(statsRes.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch AI governance telemetry';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Threat Monitoring & Alerts
  // ==========================================================================
  const fetchThreatAlerts = useCallback(async (params?: SecurityAlertQueryParams) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.getThreatAlerts(params);
      if (res.data) {
        setThreatAlerts(res.data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch security alerts';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const resolveThreatAlert = useCallback(async (alertId: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.resolveThreatAlert(alertId);
      if (res.data) {
        setThreatAlerts((prev) =>
          prev.map((alert) => (alert.id === alertId ? res.data! : alert))
        );
      }
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : `Failed to resolve alert ${alertId}`;
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ==========================================================================
  // Retention & GDPR
  // ==========================================================================
  const setRetentionPolicy = useCallback(async (payload: DataRetentionPolicyPayload): Promise<DataRetentionRuleData | undefined> => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.setRetentionPolicy(payload);
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to set retention policy';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const executeGDPRErasure = useCallback(async (payload: GDPRErasurePayload): Promise<GDPRErasureData | undefined> => {
    try {
      setLoading(true);
      setError(null);
      const res = await securityService.executeGDPRErasure(payload);
      return res.data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to execute GDPR erasure';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchCompliance();
    fetchThreatAlerts({ resolved: false });
    fetchRolesMatrix();
  }, [fetchCompliance, fetchThreatAlerts, fetchRolesMatrix]);

  return {
    compliance,
    auditLogs,
    auditTotal,
    auditPage,
    rolesMatrix,
    mfaSetup,
    mfaStatus,
    classificationResult,
    aiGovernanceLogs,
    aiGovernanceStats,
    threatAlerts,
    loading,
    error,
    fetchCompliance,
    fetchAuditLogs,
    exportAuditLogs,
    fetchRolesMatrix,
    updateRolePermissions,
    setupMFA,
    verifyMFA,
    disableMFA,
    classifyContent,
    fetchAIGovernance,
    fetchThreatAlerts,
    resolveThreatAlert,
    setRetentionPolicy,
    executeGDPRErasure,
  };
}

export default useSecurity;
