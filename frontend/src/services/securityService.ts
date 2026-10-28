/**
 * Phase 3.3 Enterprise Security, Compliance, Governance & Data Protection API Client Service.
 * Implements communication with all Phase 3.3 REST endpoints:
 * - Enterprise Login & Session Revocation
 * - TOTP MFA Setup, Verify, Disable
 * - Audit Trail Logs & Export
 * - Roles & Permissions Matrix
 * - Data Classification & PII Scanning
 * - AI Governance Logs & Stats
 * - Regulatory Compliance Overview & Retention Rules
 * - Security Threat Monitoring & Resolution
 *
 * Aligned with docs/api/api-contract.md Section 15 and devdocs/p3/p3.3.txt.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';
import type {
  AIGovernanceStatsData,
  ComplianceOverviewData,
  DataClassificationScanData,
  DataRetentionPolicyPayload,
  DataRetentionRuleData,
  DocumentClassificationStatusData,
  EnterpriseLoginData,
  EnterpriseLoginPayload,
  GDPRErasureData,
  GDPRErasurePayload,
  MFASetupData,
  MFAVerifyData,
  PaginatedAIGovernanceLogsResponse,
  PaginatedSecurityAuditLogsResponse,
  RolePermissionItem,
  SecurityThreatAlertItem,
} from '@/types/security';

export interface AuditLogQueryParams {
  page?: number;
  page_size?: number;
  action?: string;
  status?: string;
}

export interface AIGovernanceQueryParams {
  page?: number;
  page_size?: number;
  guardrail_status?: string;
}

export interface SecurityAlertQueryParams {
  unresolved_only?: boolean;
  resolved?: boolean;
}

export const securityService = {
  // ==========================================================================
  // Authentication & Session Management
  // ==========================================================================

  async enterpriseLogin(
    payload: EnterpriseLoginPayload
  ): Promise<ApiResponse<EnterpriseLoginData>> {
    const response = await apiClient.post<ApiResponse<EnterpriseLoginData>>(
      '/security/login',
      payload
    );
    return response.data;
  },

  async enterpriseLogout(): Promise<ApiResponse<{ message: string }>> {
    const response = await apiClient.post<ApiResponse<{ message: string }>>(
      '/security/logout',
      {}
    );
    return response.data;
  },

  // ==========================================================================
  // Multi-Factor Authentication (MFA / TOTP)
  // ==========================================================================

  async setupMFA(): Promise<ApiResponse<MFASetupData>> {
    const response = await apiClient.post<ApiResponse<MFASetupData>>(
      '/security/mfa/setup',
      {}
    );
    return response.data;
  },

  async verifyMFA(code: string): Promise<ApiResponse<MFAVerifyData>> {
    const response = await apiClient.post<ApiResponse<MFAVerifyData>>(
      '/security/mfa/verify',
      { code }
    );
    return response.data;
  },

  async disableMFA(code: string): Promise<ApiResponse<{ message: string }>> {
    const response = await apiClient.post<ApiResponse<{ message: string }>>(
      '/security/mfa/disable',
      { code }
    );
    return response.data;
  },

  // ==========================================================================
  // Audit Trails & Compliance Export
  // ==========================================================================

  async getAuditLogs(
    params?: AuditLogQueryParams
  ): Promise<PaginatedSecurityAuditLogsResponse> {
    const response = await apiClient.get<PaginatedSecurityAuditLogsResponse>(
      '/security/audit',
      { params }
    );
    return response.data;
  },

  async exportAuditLogs(
    format: 'json' | 'csv' = 'json',
    startDate?: string,
    endDate?: string
  ): Promise<Blob> {
    const response = await apiClient.get('/security/audit', {
      params: {
        format,
        start_date: startDate,
        end_date: endDate,
      },
      responseType: 'blob',
    });
    return response.data as Blob;
  },

  // ==========================================================================
  // Roles & Permissions Matrix
  // ==========================================================================

  async getRolesMatrix(): Promise<ApiResponse<RolePermissionItem[]>> {
    const response = await apiClient.get<ApiResponse<RolePermissionItem[]>>(
      '/security/roles'
    );
    return response.data;
  },

  async updateRolePermissions(
    role: string,
    permissions: string[]
  ): Promise<ApiResponse<RolePermissionItem>> {
    const response = await apiClient.post<ApiResponse<RolePermissionItem>>(
      '/security/permissions',
      { role, permissions }
    );
    return response.data;
  },

  // ==========================================================================
  // Sensitive Data Classification & PII Scanner
  // ==========================================================================

  async classifyData(
    content: string,
    documentId?: string
  ): Promise<ApiResponse<DataClassificationScanData>> {
    const response = await apiClient.post<ApiResponse<DataClassificationScanData>>(
      '/security/data-classification/scan',
      {
        content,
        document_id: documentId,
      }
    );
    return response.data;
  },

  async getDocumentClassification(
    documentId: string
  ): Promise<ApiResponse<DocumentClassificationStatusData>> {
    const response = await apiClient.get<ApiResponse<DocumentClassificationStatusData>>(
      `/security/data-classification/${documentId}`
    );
    return response.data;
  },

  // ==========================================================================
  // AI Governance & Safety Guardrails
  // ==========================================================================

  async getAIGovernanceLogs(
    params?: AIGovernanceQueryParams
  ): Promise<PaginatedAIGovernanceLogsResponse> {
    const response = await apiClient.get<PaginatedAIGovernanceLogsResponse>(
      '/security/ai-governance/logs',
      { params }
    );
    return response.data;
  },

  async getAIGovernanceStats(): Promise<ApiResponse<AIGovernanceStatsData>> {
    const response = await apiClient.get<ApiResponse<AIGovernanceStatsData>>(
      '/security/ai-governance/stats'
    );
    return response.data;
  },

  // ==========================================================================
  // Regulatory Compliance & Retention Policies
  // ==========================================================================

  async getComplianceOverview(): Promise<ApiResponse<ComplianceOverviewData>> {
    const response = await apiClient.get<ApiResponse<ComplianceOverviewData>>(
      '/security/compliance'
    );
    return response.data;
  },

  async setRetentionPolicy(
    payload: DataRetentionPolicyPayload
  ): Promise<ApiResponse<DataRetentionRuleData>> {
    const response = await apiClient.post<ApiResponse<DataRetentionRuleData>>(
      '/security/compliance/retention-policies',
      payload
    );
    return response.data;
  },

  async executeGDPRErasure(
    payload: GDPRErasurePayload
  ): Promise<ApiResponse<GDPRErasureData>> {
    const response = await apiClient.post<ApiResponse<GDPRErasureData>>(
      '/security/compliance/gdpr-erasure',
      payload
    );
    return response.data;
  },

  // ==========================================================================
  // Security Monitoring & Threat Alerts
  // ==========================================================================

  async getThreatAlerts(
    params?: SecurityAlertQueryParams
  ): Promise<ApiResponse<SecurityThreatAlertItem[]>> {
    const response = await apiClient.get<ApiResponse<SecurityThreatAlertItem[]>>(
      '/security/monitoring/alerts',
      { params }
    );
    return response.data;
  },

  async resolveThreatAlert(
    alertId: string
  ): Promise<ApiResponse<SecurityThreatAlertItem>> {
    const response = await apiClient.put<ApiResponse<SecurityThreatAlertItem>>(
      `/security/monitoring/alerts/${alertId}/resolve`,
      {}
    );
    return response.data;
  },
};

export default securityService;
