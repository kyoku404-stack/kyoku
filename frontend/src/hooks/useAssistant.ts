/**
 * Phase 2.3 Enterprise AI Assistant Custom React Hook.
 * Manages conversational state, multi-step task execution, HITL approvals,
 * automated reports, and proactive recommendations.
 * Author: Member 3 (Frontend Lead)
 */

import { useState, useCallback, useEffect } from 'react';
import { assistantService } from '@/services/assistantService';
import type {
  AssistantMessage,
  AssistantMetrics,
  ApprovalDecision,
  ProactiveRecommendationItem,
  ReportFormat,
  ReportGenerateResponseData,
  ReportType,
  TaskExecuteResponseData,
  WorkflowItemResponse,
} from '@/types/assistant';

export interface UseAssistantReturn {
  // Chat state
  messages: AssistantMessage[];
  activeSessionId: string | null;
  isLoading: boolean;
  error: string | null;
  sendMessage: (text: string, departmentId?: string | null, projectId?: string | null) => Promise<void>;
  startNewSession: () => void;

  // Task & Workflow state
  activeWorkflow: TaskExecuteResponseData | null;
  workflows: WorkflowItemResponse[];
  isExecutingTask: boolean;
  executeTask: (instructions: string, title?: string, context?: Record<string, unknown>) => Promise<void>;
  refreshWorkflows: () => Promise<void>;

  // HITL Approval state
  pendingApproval: TaskExecuteResponseData['pending_approval'] | null;
  isApprovalModalOpen: boolean;
  setIsApprovalModalOpen: (open: boolean) => void;
  submitApprovalDecision: (approvalId: string, decision: ApprovalDecision, reason?: string) => Promise<void>;

  // Report state
  latestReport: ReportGenerateResponseData | null;
  isReportModalOpen: boolean;
  setIsReportModalOpen: (open: boolean) => void;
  isGeneratingReport: boolean;
  generateReport: (
    reportType: ReportType,
    title: string,
    format?: ReportFormat,
    filters?: Record<string, unknown>
  ) => Promise<void>;

  // Recommendations state
  recommendations: ProactiveRecommendationItem[];
  dismissRecommendation: (id: string) => void;
  refreshRecommendations: () => Promise<void>;

  // Executive Metrics
  metrics: AssistantMetrics;
}

const INITIAL_METRICS: AssistantMetrics = {
  active_workflows: 2,
  pending_approvals: 1,
  tasks_automated: 48,
  reports_generated: 16,
};

const DEFAULT_RECOMMENDATIONS: ProactiveRecommendationItem[] = [
  {
    id: 'rec_freq_001',
    category: 'FREQUENT_DOCUMENTS',
    title: 'Employee Handbook 2026',
    description: 'Consistently top-ranked document with 84 queries this month.',
    suggested_action: 'Pin document to departmental workspace home',
  },
  {
    id: 'rec_gap_002',
    category: 'MISSING_DOCUMENTATION',
    title: 'Remote Equipment Reimbursement Policy',
    description: 'Detected 12 queries regarding monitor stipends with low grounding confidence.',
    suggested_action: 'Request HR to author and upload reimbursement policy',
  },
  {
    id: 'rec_dup_003',
    category: 'DUPLICATE_KNOWLEDGE',
    title: 'Information Security Guidelines v1.2 vs v2.0',
    description: 'High semantic similarity (>92%) detected between two active versions.',
    suggested_action: 'Archive v1.2 to eliminate retrieval ambiguity',
  },
  {
    id: 'rec_inact_004',
    category: 'INACTIVE_PROJECTS',
    title: 'Project Falcon Q1 Migration',
    description: 'Workspace has observed zero document updates or user queries for 90 days.',
    suggested_action: 'Archive project workspace to maintain clean search index',
  },
];

export function useAssistant(): UseAssistantReturn {
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: 'm_welcome',
      role: 'assistant',
      content:
        'Hello! I am your Enterprise AI Assistant. I can help answer policy questions, plan multi-step workflows, generate executive reports, or automate routine organizational tasks.',
      created_at: new Date().toISOString(),
    },
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [activeWorkflow, setActiveWorkflow] = useState<TaskExecuteResponseData | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowItemResponse[]>([]);
  const [isExecutingTask, setIsExecutingTask] = useState<boolean>(false);

  const [pendingApproval, setPendingApproval] = useState<
    TaskExecuteResponseData['pending_approval'] | null
  >(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState<boolean>(false);

  const [latestReport, setLatestReport] = useState<ReportGenerateResponseData | null>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState<boolean>(false);

  const [recommendations, setRecommendations] = useState<ProactiveRecommendationItem[]>(
    DEFAULT_RECOMMENDATIONS
  );
  const [metrics, setMetrics] = useState<AssistantMetrics>(INITIAL_METRICS);

  // Send conversational prompt
  const sendMessage = useCallback(
    async (text: string, departmentId?: string | null, projectId?: string | null) => {
      if (!text.trim()) return;

      const userMsg: AssistantMessage = {
        id: `usr_${Date.now()}`,
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await assistantService.chat({
          message: text,
          session_id: activeSessionId,
          department_id: departmentId,
          project_id: projectId,
        });

        if (response.success && response.data) {
          const data = response.data;
          setActiveSessionId(data.session_id);

          const asstMsg: AssistantMessage = {
            id: data.message_id || `asst_${Date.now()}`,
            role: 'assistant',
            content: data.reply,
            intent: data.detected_intent,
            tools_executed: data.tools_executed,
            requires_approval: data.requires_approval,
            approval_id: data.approval_id,
            created_at: data.created_at,
          };
          setMessages((prev) => [...prev, asstMsg]);

          if (data.requires_approval && data.approval_id) {
            setPendingApproval({
              approval_id: data.approval_id,
              step_number: 1,
              action_type: data.tools_executed[0] || 'SensitiveTool',
              description: data.reply,
              payload: { message: text },
              status: 'PENDING',
            });
            setIsApprovalModalOpen(true);
            setMetrics((prev) => ({
              ...prev,
              pending_approvals: prev.pending_approvals + 1,
            }));
          }

          setMetrics((prev) => ({
            ...prev,
            tasks_automated: prev.tasks_automated + (data.tools_executed.length > 0 ? 1 : 0),
          }));
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : 'Failed to send message to assistant';
        setError(errMsg);
        setMessages((prev) => [
          ...prev,
          {
            id: `err_${Date.now()}`,
            role: 'assistant',
            content: `Error: ${errMsg}. Please try again.`,
            created_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [activeSessionId]
  );

  // Execute explicit multi-step task
  const executeTask = useCallback(
    async (instructions: string, title?: string, context?: Record<string, unknown>) => {
      if (!instructions.trim()) return;

      setIsExecutingTask(true);
      setError(null);

      try {
        const response = await assistantService.executeTask({
          instructions,
          title,
          session_id: activeSessionId,
          context,
        });

        if (response.success && response.data) {
          const data = response.data;
          setActiveWorkflow(data);

          if (data.pending_approval) {
            setPendingApproval(data.pending_approval);
            setIsApprovalModalOpen(true);
            setMetrics((prev) => ({
              ...prev,
              pending_approvals: prev.pending_approvals + 1,
            }));
          }

          setMetrics((prev) => ({
            ...prev,
            tasks_automated: prev.tasks_automated + data.completed_steps,
          }));
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : 'Failed to execute task plan';
        setError(errMsg);
      } finally {
        setIsExecutingTask(false);
      }
    },
    [activeSessionId]
  );

  // Submit approval decision
  const submitApprovalDecision = useCallback(
    async (approvalId: string, decision: ApprovalDecision, reason?: string) => {
      try {
        const res = await assistantService.processApproval({
          approval_id: approvalId,
          decision,
          reason,
        });

        if (res.success) {
          setIsApprovalModalOpen(false);
          setPendingApproval(null);

          // Update active workflow status if matching
          if (activeWorkflow) {
            setActiveWorkflow((prev) =>
              prev
                ? {
                    ...prev,
                    status: decision === 'APPROVED' ? 'COMPLETED' : 'CANCELLED',
                  }
                : null
            );
          }

          setMetrics((prev) => ({
            ...prev,
            pending_approvals: Math.max(0, prev.pending_approvals - 1),
          }));
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : 'Failed to submit approval decision';
        setError(errMsg);
      }
    },
    [activeWorkflow]
  );

  // Generate Report
  const generateReport = useCallback(
    async (
      reportType: ReportType,
      title: string,
      format: ReportFormat = 'MARKDOWN',
      filters?: Record<string, unknown>
    ) => {
      setIsGeneratingReport(true);
      setError(null);

      try {
        const res = await assistantService.generateReport({
          report_type: reportType,
          title,
          format,
          filters,
        });

        if (res.success && res.data) {
          setLatestReport(res.data);
          setIsReportModalOpen(true);
          setMetrics((prev) => ({
            ...prev,
            reports_generated: prev.reports_generated + 1,
          }));
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : 'Failed to generate report';
        setError(errMsg);
      } finally {
        setIsGeneratingReport(false);
      }
    },
    []
  );

  // Workflows query
  const refreshWorkflows = useCallback(async () => {
    try {
      const res = await assistantService.getWorkflows();
      if (res.success && res.data) {
        setWorkflows(res.data.workflows);
      }
    } catch {
      // Graceful fallback
    }
  }, []);

  // Recommendations query
  const refreshRecommendations = useCallback(async () => {
    try {
      const res = await assistantService.getRecommendations();
      if (res.success && res.data) {
        setRecommendations(res.data.recommendations);
      }
    } catch {
      // Retain default recommendations on error
    }
  }, []);

  const dismissRecommendation = useCallback((id: string) => {
    setRecommendations((prev) => prev.filter((r) => r.id !== id));
  }, []);

  const startNewSession = useCallback(() => {
    setActiveSessionId(null);
    setMessages([
      {
        id: `m_welcome_${Date.now()}`,
        role: 'assistant',
        content: 'New session started. How can I assist you with your enterprise tasks today?',
        created_at: new Date().toISOString(),
      },
    ]);
  }, []);

  useEffect(() => {
    refreshWorkflows();
    refreshRecommendations();
  }, [refreshWorkflows, refreshRecommendations]);

  return {
    messages,
    activeSessionId,
    isLoading,
    error,
    sendMessage,
    startNewSession,

    activeWorkflow,
    workflows,
    isExecutingTask,
    executeTask,
    refreshWorkflows,

    pendingApproval,
    isApprovalModalOpen,
    setIsApprovalModalOpen,
    submitApprovalDecision,

    latestReport,
    isReportModalOpen,
    setIsReportModalOpen,
    isGeneratingReport,
    generateReport,

    recommendations,
    dismissRecommendation,
    refreshRecommendations,

    metrics,
  };
}
