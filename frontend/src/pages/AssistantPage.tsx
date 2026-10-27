/**
 * KEEP Enterprise Platform — Enterprise AI Assistant & Agentic Workflows Page (Phase 2.3).
 *
 * Integrated digital coworker command center combining NLU intent detection,
 * DAG task planning, enterprise tool orchestration, Human-in-the-Loop approvals,
 * automated report synthesis, and proactive organizational recommendations.
 *
 * Specification: devdocs/p2/p2.3.txt Chapters 1-20 & docs/api/api-contract.md Section 10
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { useAssistant } from '@/hooks/useAssistant';
import {
  AssistantMetricsBanner,
  AssistantChatBox,
  WorkflowVisualizer,
  ApprovalModal,
  ReportViewer,
  RecommendationsWidget,
} from '@/features/assistant';
import { Bot, FileSpreadsheet, RefreshCw, Zap } from 'lucide-react';

export const AssistantPage: React.FC = () => {
  const {
    messages,
    isLoading,
    sendMessage,
    startNewSession,

    activeWorkflow,
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
  } = useAssistant();

  const handleQuickTask = () => {
    executeTask(
      'Audit all quarterly documents and compile a compliance summary report',
      'Quarterly Compliance Audit',
      { category: 'COMPLIANCE', max_docs: 5 }
    );
  };

  return (
    <div className="flex-1 min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md sticky top-0 z-20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold text-white tracking-tight">Enterprise AI Assistant</h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Phase 2.3
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Agentic task execution, DAG workflows, tool calls & human-in-the-loop governance
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={handleQuickTask}
              className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 hover:border-slate-700 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 text-amber-400" /> Run Quick Audit
            </button>

            <button
              type="button"
              onClick={() => setIsReportModalOpen(true)}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-1.5"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" /> Generate Report
            </button>

            <button
              type="button"
              onClick={() => {
                refreshWorkflows();
                refreshRecommendations();
              }}
              className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
              title="Refresh telemetry"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Executive Metrics Banner */}
        <AssistantMetricsBanner
          metrics={metrics}
          onRefresh={() => {
            refreshWorkflows();
            refreshRecommendations();
          }}
        />

        {/* Proactive Recommendations */}
        <RecommendationsWidget
          recommendations={recommendations}
          onDismiss={dismissRecommendation}
          onApplyAction={(rec) => {
            sendMessage(`Execute proactive recommendation: ${rec.title}`);
          }}
        />

        {/* Command Center 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Left Column: Conversational Assistant Chat */}
          <div className="lg:col-span-2">
            <AssistantChatBox
              messages={messages}
              isLoading={isLoading}
              onSendMessage={sendMessage}
              onOpenApprovalModal={() => setIsApprovalModalOpen(true)}
              onNewSession={startNewSession}
            />
          </div>

          {/* Right Column: Active DAG Workflow Visualizer */}
          <div className="lg:col-span-1 space-y-4">
            <WorkflowVisualizer
              workflow={activeWorkflow}
              onOpenApproval={() => setIsApprovalModalOpen(true)}
            />
          </div>
        </div>
      </main>

      {/* HITL Approval Modal */}
      <ApprovalModal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        approval={pendingApproval}
        onDecision={submitApprovalDecision}
      />

      {/* Report Viewer / Generator Modal */}
      <ReportViewer
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        report={latestReport}
        onGenerateReport={generateReport}
        isGenerating={isGeneratingReport}
      />
    </div>
  );
};

export default AssistantPage;
