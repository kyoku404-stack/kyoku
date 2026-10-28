/**
 * KEEP Enterprise Platform — Centralized Type Exports.
 * Updated for Phase 1.5 Organization & Workspace Management alignment.
 */

export * from './api';
export * from './auth';
export * from './user';
export * from './organization';
export * from './department';
export * from './team';
export * from './project';
export * from './invitation';
export * from './member';
export * from './document';
export * from './search';
export * from './chat';
export * from './analytics';
export * from './health';
export * from './theme';
export * from './meeting';
export * from './task';
export type {
  KgEntity,
  KgRelationship,
  KgEntityCreate,
  KgRelationshipCreate,
  KgQueryRequest,
  KgQueryResponse,
} from './knowledge';
export * from './activity';
export * from './permission';
export * from './audit';
export * from './dashboard';
export * from './observability';
export * from './ingestion';
export * from './rag';
export * from './assistant';
export * from './graph';
export type {
  HealthScoreRating,
  AnomalySeverity,
  AnomalyType,
  IntelligenceRecommendationCategory,
  RecommendationStatus,
  DepartmentHealthScoreItem,
  HealthScoreBreakdown,
  KPIsResponse,
  ExecutiveDashboardResponse,
  TrendPointItem,
  DepartmentActivityItem,
  TrendAnalysisResponse,
  DocumentForecastItem,
  StorageRunwayItem,
  QueryVolumeForecastItem,
  PredictionsResponse,
  AnomalyResponseItem,
  AnomaliesResponse,
  RecommendationResponseItem,
  RecommendationsResponse,
  KnowledgeHealthResponse,
} from './intelligence';
export * from './connector';
export * from './collaboration';
export * from './security';
export type {
  WorkflowTriggerType,
  WorkflowExecutionStatus,
  WorkflowStepAction,
  NotificationChannel,
  NotificationPriority,
  NotificationCategory,
  WorkflowConditionRule,
  WorkflowRetryPolicy,
  WorkflowStepItem,
  WorkflowItem,
  WorkflowCreatePayload,
  WorkflowUpdatePayload,
  WorkflowExecutionStepItem,
  WorkflowExecutionItem,
  WorkflowApprovalItem,
  WorkflowApprovalDecisionPayload,
  NotificationPreferenceItem,
  NotificationPreferenceUpdatePayload,
  WorkflowTemplateItem,
  WorkflowAnalyticsData,
  ApprovalDecision as WorkflowApprovalDecision,
  WorkflowStatus as AutomationWorkflowStatus,
  ApprovalStatus as WorkflowApprovalStatus,
  NotificationItem as EnterpriseNotificationItem,
} from './workflow';

