/**
 * Phase 3.4 Workflow Automation & Event-Driven Intelligence Master Page.
 * Centralized platform hub for managing automated DAG workflows, human approvals,
 * template blueprints, and multi-channel notifications.
 *
 * Aligned with docs/api/api-contract.md Section 16 & devdocs/p3/p3.4.txt.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  Zap,
  UserCheck,
  Sparkles,
  BarChart3,
  CheckCircle,
} from 'lucide-react';
import { useWorkflow } from '@/hooks/useWorkflow';
import {
  WorkflowMetricsBanner,
  WorkflowListTable,
  CreateWorkflowModal,
  WorkflowApprovalQueue,
  NotificationCenterDrawer,
  NotificationPreferencesModal,
  WorkflowTemplateGallery,
  WorkflowAnalyticsDashboard,
} from '@/features/workflow';
import type { WorkflowCreatePayload } from '@/types/workflow';

type WorkflowTab = 'workflows' | 'approvals' | 'templates' | 'analytics';

export const WorkflowAutomationPage: React.FC = () => {
  const {
    workflows,
    pendingApprovals,
    templates,
    analytics,
    notifications,
    unreadNotificationsCount,
    preferences,
    loading,
    error,
    fetchWorkflows,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    executeWorkflow,
    fetchExecutions,
    fetchPendingApprovals,
    decideApproval,
    fetchTemplates,
    fetchAnalytics,
    fetchNotifications,
    markNotificationRead,
    markAllNotificationsRead,
    fetchNotificationPreferences,
    updateNotificationPreferences,
  } = useWorkflow();

  const [activeTab, setActiveTab] = useState<WorkflowTab>('workflows');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isPreferencesModalOpen, setIsPreferencesModalOpen] = useState(false);
  const [isNotificationsDrawerOpen, setIsNotificationsDrawerOpen] = useState(false);
  const [isExecutingId, setIsExecutingId] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  const handleExecuteWorkflow = async (id: string) => {
    try {
      setIsExecutingId(id);
      await executeWorkflow(id);
      setActionSuccessMessage('Workflow execution triggered successfully!');
      setTimeout(() => setActionSuccessMessage(null), 4000);
    } catch {
      // Error handled by hook
    } finally {
      setIsExecutingId(null);
    }
  };

  const handleToggleActive = async (id: string, currentActive: boolean) => {
    try {
      await updateWorkflow(id, { is_active: !currentActive });
    } catch {
      // Error handled by hook
    }
  };

  const handleDeleteWorkflow = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      await deleteWorkflow(id);
    }
  };

  const handleDeployTemplate = async (payload: WorkflowCreatePayload) => {
    try {
      await createWorkflow(payload);
      setActiveTab('workflows');
      setActionSuccessMessage(`Deployed template "${payload.name}" successfully!`);
      setTimeout(() => setActionSuccessMessage(null), 4000);
    } catch {
      // Error handled by hook
    }
  };

  const handleRefreshAll = () => {
    fetchWorkflows();
    fetchPendingApprovals();
    fetchTemplates();
    fetchAnalytics();
    fetchNotifications();
    fetchNotificationPreferences();
  };

  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-900 p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Metrics Banner */}
      <WorkflowMetricsBanner
        analytics={analytics}
        pendingApprovalsCount={pendingApprovals.length}
        unreadNotificationsCount={unreadNotificationsCount}
        onOpenCreateModal={() => setIsCreateModalOpen(true)}
        onOpenPreferencesModal={() => setIsPreferencesModalOpen(true)}
        onOpenNotificationsDrawer={() => setIsNotificationsDrawerOpen(true)}
        onRefresh={handleRefreshAll}
        isLoading={loading}
      />

      {/* Success Notification Alert */}
      {actionSuccessMessage && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl text-emerald-700 dark:text-emerald-300 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold">{actionSuccessMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setActionSuccessMessage(null)}
            className="text-emerald-600 hover:text-emerald-800 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Global Error Alert */}
      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between shadow-xs">
          <span>{error}</span>
          <button
            type="button"
            onClick={handleRefreshAll}
            className="text-rose-600 hover:text-rose-800 underline font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('workflows')}
          className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'workflows'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Workflows ({workflows.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('approvals')}
          className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'approvals'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          <span>Approvals ({pendingApprovals.length})</span>
          {pendingApprovals.length > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-400 text-amber-950 font-bold">
              {pendingApprovals.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('templates')}
          className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'templates'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Templates ({templates.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('analytics')}
          className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'analytics'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Analytics & Telemetry</span>
        </button>
      </div>

      {/* Tab Content Panes */}
      {activeTab === 'workflows' && (
        <WorkflowListTable
          workflows={workflows}
          onExecute={handleExecuteWorkflow}
          onToggleActive={handleToggleActive}
          onDelete={handleDeleteWorkflow}
          onSelectWorkflow={(w) => {
            fetchExecutions(w.id);
          }}
          isExecutingId={isExecutingId}
        />
      )}

      {activeTab === 'approvals' && (
        <WorkflowApprovalQueue
          approvals={pendingApprovals}
          onDecide={decideApproval}
          isLoading={loading}
        />
      )}

      {activeTab === 'templates' && (
        <WorkflowTemplateGallery
          templates={templates}
          onSelectTemplate={handleDeployTemplate}
        />
      )}

      {activeTab === 'analytics' && (
        <WorkflowAnalyticsDashboard analytics={analytics} />
      )}

      {/* Modals & Slide-Overs */}
      <CreateWorkflowModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={createWorkflow}
      />

      <NotificationCenterDrawer
        isOpen={isNotificationsDrawerOpen}
        onClose={() => setIsNotificationsDrawerOpen(false)}
        notifications={notifications}
        unreadCount={unreadNotificationsCount}
        onMarkRead={markNotificationRead}
        onMarkAllRead={markAllNotificationsRead}
      />

      <NotificationPreferencesModal
        isOpen={isPreferencesModalOpen}
        onClose={() => setIsPreferencesModalOpen(false)}
        preferences={preferences}
        onUpdatePreference={updateNotificationPreferences}
      />
    </div>
  );
};
