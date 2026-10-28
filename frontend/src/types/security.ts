/**
 * Phase 3.3 Enterprise Security, Compliance, Governance & Data Protection TypeScript Definitions.
 * Aligned with docs/api/api-contract.md Section 15 and devdocs/p3/p3.3.txt.
 * Author: Member 3 (Frontend & UI Lead)
 */

export const ClassificationLevel = {
  PUBLIC: 'PUBLIC',
  INTERNAL: 'INTERNAL',
  CONFIDENTIAL: 'CONFIDENTIAL',
  RESTRICTED: 'RESTRICTED',
} as const;
export type ClassificationLevel = (typeof ClassificationLevel)[keyof typeof ClassificationLevel];

export const AuditStatus = {
  SUCCESS: 'SUCCESS',
  FAILURE: 'FAILURE',
  DENIED: 'DENIED',
} as const;
export type AuditStatus = (typeof AuditStatus)[keyof typeof AuditStatus];

export const ComplianceStandard = {
  GDPR: 'GDPR',
  ISO_27001: 'ISO_27001',
  SOC_2: 'SOC_2',
  HIPAA: 'HIPAA',
} as const;
export type ComplianceStandard = (typeof ComplianceStandard)[keyof typeof ComplianceStandard];

export const ComplianceStatus = {
  COMPLIANT: 'COMPLIANT',
  PARTIAL: 'PARTIAL',
  NON_COMPLIANT: 'NON_COMPLIANT',
} as const;
export type ComplianceStatus = (typeof ComplianceStatus)[keyof typeof ComplianceStatus];

export const SecurityAlertSeverity = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL',
} as const;
export type SecurityAlertSeverity = (typeof SecurityAlertSeverity)[keyof typeof SecurityAlertSeverity];

export const SecurityAlertType = {
  FAILED_LOGIN_SPIKE: 'FAILED_LOGIN_SPIKE',
  PROMPT_INJECTION_ATTEMPT: 'PROMPT_INJECTION_ATTEMPT',
  SUSPICIOUS_EXPORT: 'SUSPICIOUS_EXPORT',
  BRUTE_FORCE: 'BRUTE_FORCE',
  PRIVILEGE_ESCALATION: 'PRIVILEGE_ESCALATION',
} as const;
export type SecurityAlertType = (typeof SecurityAlertType)[keyof typeof SecurityAlertType];

export const GuardrailStatus = {
  PASSED: 'PASSED',
  FLAGGED: 'FLAGGED',
  BLOCKED: 'BLOCKED',
} as const;
export type GuardrailStatus = (typeof GuardrailStatus)[keyof typeof GuardrailStatus];

// ============================================================================
// 15.1 Enterprise Authentication & Session Management
// ============================================================================

export interface EnterpriseLoginPayload {
  email: string;
  password: string;
  provider?: string;
  sso_token?: string | null;
}

export interface EnterpriseLoginData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  organization_id: string;
  role: string;
  mfa_required: boolean;
  mfa_verified: boolean;
}

// ============================================================================
// 15.2 Multi-Factor Authentication (MFA / TOTP)
// ============================================================================

export interface MFASetupData {
  secret_key: string;
  otpauth_uri: string;
  backup_codes: string[];
}

export interface MFAVerifyData {
  is_enabled: boolean;
  mfa_verified: boolean;
}

// ============================================================================
// 15.3 Enterprise Audit Trails
// ============================================================================

export interface SecurityAuditLogItem {
  id: string;
  organization_id: string;
  user_id?: string | null;
  action: string;
  resource: string;
  resource_id?: string | null;
  ip_address: string;
  user_agent?: string | null;
  status: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface PaginatedSecurityAuditLogsResponse {
  success: boolean;
  total: number;
  page: number;
  page_size: number;
  data: SecurityAuditLogItem[];
}

// ============================================================================
// 15.4 Roles & Permissions Management
// ============================================================================

export interface RolePermissionItem {
  role: string;
  description: string;
  permissions: string[];
}

// ============================================================================
// 15.5 Sensitive Data Classification & PII Scanner
// ============================================================================

export interface DetectedPIIEntityItem {
  type: string;
  count: number;
  masked_sample: string;
}

export interface DataClassificationScanData {
  document_id?: string | null;
  classification_level: ClassificationLevel;
  detected_pii_entities: DetectedPIIEntityItem[];
  pii_count: number;
  confidence_score: number;
  redacted_preview: string;
}

export interface DocumentClassificationStatusData {
  document_id: string;
  classification_level: ClassificationLevel;
  pii_count: number;
  confidence_score: number;
  scanned_at: string;
}

// ============================================================================
// 15.6 AI Governance & Safety Guardrails
// ============================================================================

export interface AIGovernanceLogItem {
  id: string;
  user_id?: string | null;
  prompt_snippet: string;
  model_name: string;
  guardrail_status: string;
  token_usage: number;
  latency_ms: number;
  created_at: string;
}

export interface AIGovernanceStatsData {
  total_queries_audited: number;
  guardrail_blocks: number;
  avg_latency_ms: number;
  prompt_injection_attempts: number;
  safety_score_percentage: number;
}

// ============================================================================
// 15.7 Enterprise Compliance Framework
// ============================================================================

export interface ComplianceStandardScoreItem {
  standard: string;
  score: number;
  status: string;
  controls_passed: number;
  controls_total: number;
}

export interface ComplianceOverviewData {
  overall_compliance_score: number;
  standards: ComplianceStandardScoreItem[];
}

export interface DataRetentionPolicyPayload {
  resource_type: string;
  retention_days: number;
  action_on_expiry: string;
}

export interface GDPRErasurePayload {
  target_user_id: string;
  reason?: string;
}

export interface GDPRErasureData {
  erasure_id: string;
  completed_at: string;
}

export interface DataRetentionRuleData {
  rule_id: string;
  resource_type: string;
  retention_days: number;
  action_on_expiry: string;
  updated_at: string;
}

export interface PaginatedAIGovernanceLogsResponse {
  success: boolean;
  total: number;
  page: number;
  page_size: number;
  data: AIGovernanceLogItem[];
}

export interface SecurityThreatAlertItem {
  id: string;
  alert_type: string;
  severity: SecurityAlertSeverity;
  description: string;
  source_ip: string;
  resolved: boolean;
  triggered_at: string;
}
