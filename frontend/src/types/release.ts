/**
 * KEEP Enterprise Platform — Phase 3.7 Release & Security Audit Type Definitions.
 *
 * Aligned with backend contracts:
 * - devdocs/p3/p3.7.txt Section 19
 * - docs/api/api-contract.md
 * - backend/app/schemas/release.py
 *
 * Author: Member 3 (Frontend & UI Lead)
 */

export type PreflightCheckCategory = 'PERSISTENCE' | 'CACHE' | 'STORAGE' | 'AI_INFRA' | 'GOVERNANCE';
export type CheckStatus = 'PASSED' | 'FAILED' | 'WARNING' | 'SKIPPED';
export type ReleaseStatus = 'PENDING' | 'DEPLOYING' | 'COMPLETED' | 'FAILED' | 'ROLLED_BACK';
export type AuditSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export interface PreflightCheckDetail {
  check_name: string;
  category: PreflightCheckCategory | string;
  status: CheckStatus;
  score: number;
  details: Record<string, unknown>;
  verified_at: string;
}

export interface SystemReadinessData {
  is_ready: boolean;
  overall_score: number;
  evaluated_at: string;
  target_version: string;
  git_commit: string;
  checks: PreflightCheckDetail[];
  failing_checks: string[];
}

export interface SystemReadinessResponse {
  success: boolean;
  message: string;
  data: SystemReadinessData;
}

export interface ReleaseDeployRequest {
  version: string;
  release_tag: string;
  changelog: string;
  environment?: string;
  enforce_preflight?: boolean;
}

export interface ReleaseDeployData {
  release_id: string;
  version: string;
  release_tag: string;
  git_commit: string;
  status: ReleaseStatus;
  preflight_score: number;
  deployed_by?: string | null;
  started_at: string;
  completed_at?: string | null;
  changelog: string;
  artifacts: Record<string, unknown>;
}

export interface ReleaseDeployResponse {
  success: boolean;
  message: string;
  data: ReleaseDeployData;
}

export interface ReleaseHistoryItemData {
  release_id: string;
  version: string;
  release_tag: string;
  git_commit: string;
  status: ReleaseStatus;
  preflight_score: number;
  deployed_by?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ReleaseHistoryResponse {
  success: boolean;
  data: ReleaseHistoryItemData[];
}

export interface SecurityControlData {
  control_id: string;
  name: string;
  status: CheckStatus;
  severity: AuditSeverity;
  description: string;
  mitigation: string;
}

export interface SecurityFindingData {
  finding_id: string;
  control_id: string;
  severity: AuditSeverity;
  title: string;
  remediation: string;
  resolved: boolean;
}

export interface SecurityAuditData {
  compliance_standard: string;
  overall_compliance_percent: number;
  evaluated_at: string;
  total_controls: number;
  passed_controls: number;
  failed_controls: number;
  controls: SecurityControlData[];
  findings: SecurityFindingData[];
}

export interface SecurityAuditResponse {
  success: boolean;
  message: string;
  data: SecurityAuditData;
}

