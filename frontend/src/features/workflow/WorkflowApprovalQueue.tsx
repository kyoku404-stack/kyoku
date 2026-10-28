/**
 * Phase 3.4 WorkflowApprovalQueue Component.
 * Displays pending human-in-the-loop approvals with decision controls (Approve/Reject).
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  Clock,
  UserCheck,
  ShieldAlert,
} from 'lucide-react';
import type { ApprovalDecision, WorkflowApprovalItem } from '@/types/workflow';

interface WorkflowApprovalQueueProps {
  approvals: WorkflowApprovalItem[];
  onDecide: (approvalId: string, decision: ApprovalDecision, comments?: string) => Promise<unknown>;
  isLoading: boolean;
}

export const WorkflowApprovalQueue: React.FC<WorkflowApprovalQueueProps> = ({
  approvals,
  onDecide,
  isLoading,
}) => {
  const [selectedApproval, setSelectedApproval] = useState<WorkflowApprovalItem | null>(null);
  const [decision, setDecision] = useState<ApprovalDecision>('approved');
  const [comments, setComments] = useState('');
  const [isDeciding, setIsDeciding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openDecisionModal = (approval: WorkflowApprovalItem, dec: ApprovalDecision) => {
    setSelectedApproval(approval);
    setDecision(dec);
    setComments('');
    setError(null);
  };

  const closeDecisionModal = () => {
    setSelectedApproval(null);
    setComments('');
    setError(null);
  };

  const handleConfirmDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;

    try {
      setIsDeciding(true);
      setError(null);
      await onDecide(selectedApproval.id, decision, comments.trim() || undefined);
      closeDecisionModal();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to record approval decision');
    } finally {
      setIsDeciding(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-amber-500" />
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Human-in-the-Loop Approval Queue
          </h2>
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
            {approvals.length} pending
          </span>
        </div>
      </div>

      {/* Queue Body */}
      {approvals.length === 0 ? (
        <div className="py-10 text-center text-slate-500 dark:text-slate-400">
          <Clock className="w-8 h-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
          <p className="text-sm font-medium">No pending approvals</p>
          <p className="text-xs text-slate-400 mt-1">
            Workflows requiring human sign-off will pause and appear here automatically.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {approvals.map((approval) => (
            <div
              key={approval.id}
              className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">
                    {approval.workflow_name || `Workflow ${approval.execution_id.slice(0, 8)}`}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                    Step: {approval.step_name || 'Approval Gate'}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
                  <span>Execution: <code className="font-mono">{approval.execution_id.slice(0, 8)}...</code></span>
                  <span>Requested: {new Date(approval.created_at).toLocaleTimeString()}</span>
                  {approval.expires_at && (
                    <span className="text-rose-500">
                      Expires: {new Date(approval.expires_at).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => openDecisionModal(approval, 'approved')}
                  disabled={isLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 rounded-lg transition-colors"
                >
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>Approve</span>
                </button>
                <button
                  type="button"
                  onClick={() => openDecisionModal(approval, 'rejected')}
                  disabled={isLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/60 hover:bg-rose-100 dark:hover:bg-rose-900/60 rounded-lg transition-colors"
                >
                  <XCircle className="w-4 h-4 text-rose-600" />
                  <span>Reject</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Decision Modal */}
      {selectedApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="w-full max-w-md bg-white dark:bg-slate-850 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                  decision === 'approved'
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600'
                    : 'bg-rose-50 dark:bg-rose-950/60 text-rose-600'
                }`}
              >
                {decision === 'approved' ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <XCircle className="w-5 h-5" />
                )}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white capitalize">
                  {decision} Workflow Step
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Provide optional audit commentary before resuming execution.
                </p>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleConfirmDecision} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Comments / Justification
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  rows={3}
                  placeholder={`Reason for ${decision}...`}
                  className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={closeDecisionModal}
                  className="px-3.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isDeciding}
                  className={`px-4 py-1.5 text-xs font-semibold text-white rounded-lg shadow-sm transition-colors ${
                    decision === 'approved'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {isDeciding ? 'Submitting...' : `Confirm ${decision}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
