import React, { useState } from 'react';
import { ShieldAlert, Check, X, AlertTriangle } from 'lucide-react';
import type { ApprovalDecision, TaskExecuteResponseData } from '@/types/assistant';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  approval: TaskExecuteResponseData['pending_approval'] | null;
  onDecision: (approvalId: string, decision: ApprovalDecision, reason?: string) => Promise<void>;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  isOpen,
  onClose,
  approval,
  onDecision,
}) => {
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  if (!isOpen || !approval) return null;

  const handleAction = async (decision: ApprovalDecision) => {
    setIsSubmitting(true);
    try {
      await onDecision(approval.approval_id, decision, reason);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl text-slate-200">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Human Approval Required</h3>
            <p className="text-xs text-slate-400">
              Action: <span className="font-semibold text-amber-400">{approval.action_type}</span>
            </p>
          </div>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg mb-4 text-xs space-y-2">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
            <p className="text-slate-300 font-medium">{approval.description}</p>
          </div>

          {approval.payload && (
            <div className="mt-2 pt-2 border-t border-slate-800/80">
              <span className="text-[10px] uppercase font-bold text-slate-500">Operation Payload:</span>
              <pre className="mt-1 p-2 bg-slate-900 rounded text-[11px] text-slate-400 overflow-x-auto font-mono">
                {JSON.stringify(approval.payload, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="mb-4">
          <label className="block text-xs font-semibold text-slate-400 mb-1">
            Review Justification / Comment (Optional)
          </label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Verified by compliance policy..."
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleAction('REJECTED')}
            className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold text-xs rounded-lg transition-colors flex items-center gap-1.5"
          >
            <X className="w-3.5 h-3.5" /> Reject Action
          </button>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleAction('APPROVED')}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-1.5"
          >
            <Check className="w-3.5 h-3.5" /> Confirm & Execute
          </button>
        </div>
      </div>
    </div>
  );
};
