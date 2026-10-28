/**
 * Phase 3.4 CreateWorkflowModal Component.
 * Interactive multi-step dialog for constructing DAG workflow triggers, condition predicates, and actions.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  Plus,
  Trash2,
  Zap,
  ShieldAlert,
} from 'lucide-react';
import type {
  WorkflowConditionRule,
  WorkflowCreatePayload,
  WorkflowStepAction,
  WorkflowTriggerType,
} from '@/types/workflow';

interface CreateWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: WorkflowCreatePayload) => Promise<unknown>;
}

export const CreateWorkflowModal: React.FC<CreateWorkflowModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [triggerType, setTriggerType] = useState<WorkflowTriggerType>('document_created');
  const [isActive, setIsActive] = useState(true);

  // Condition rules
  const [conditions, setConditions] = useState<WorkflowConditionRule[]>([]);

  // Workflow steps
  const [steps, setSteps] = useState<
    Array<{
      step_order: number;
      name: string;
      action_type: WorkflowStepAction;
      action_config: Record<string, unknown>;
    }>
  >([
    {
      step_order: 1,
      name: 'Initial Action',
      action_type: 'send_notification',
      action_config: { channel: 'in_app', title: 'Automated Event Notification', message: 'Workflow triggered.' },
    },
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAddCondition = () => {
    setConditions((prev) => [
      ...prev,
      { field: 'category', operator: 'equals', value: 'confidential' },
    ]);
  };

  const handleRemoveCondition = (idx: number) => {
    setConditions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleUpdateCondition = (
    idx: number,
    field: string,
    operator: WorkflowConditionRule['operator'],
    value: string
  ) => {
    setConditions((prev) =>
      prev.map((c, i) => (i === idx ? { field, operator, value } : c))
    );
  };

  const handleAddStep = () => {
    setSteps((prev) => [
      ...prev,
      {
        step_order: prev.length + 1,
        name: `Step ${prev.length + 1}`,
        action_type: 'send_notification',
        action_config: { channel: 'in_app', title: 'Step completed', message: 'Action succeeded.' },
      },
    ]);
  };

  const handleRemoveStep = (idx: number) => {
    if (steps.length <= 1) return;
    setSteps((prev) =>
      prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_order: i + 1 }))
    );
  };

  const handleUpdateStep = (
    idx: number,
    field: string,
    val: unknown
  ) => {
    setSteps((prev) =>
      prev.map((s, i) => {
        if (i !== idx) return s;
        if (field === 'action_type') {
          let defaultConfig: Record<string, unknown> = {};
          if (val === 'send_notification') {
            defaultConfig = { channel: 'in_app', title: 'Notification', message: 'Workflow alert' };
          } else if (val === 'invoke_llm') {
            defaultConfig = { prompt_template: 'Summarize the document: {{document.title}}' };
          } else if (val === 'http_webhook') {
            defaultConfig = { url: 'https://api.external.com/webhook', method: 'POST' };
          } else if (val === 'trigger_connector_sync') {
            defaultConfig = { connector_type: 'google_drive' };
          } else if (val === 'request_approval') {
            defaultConfig = { role: 'Manager', prompt: 'Please review and approve this workflow step' };
          } else if (val === 'execute_rag_query') {
            defaultConfig = { query_template: 'Key takeaways from {{document.title}}' };
          }
          return { ...s, action_type: val as WorkflowStepAction, action_config: defaultConfig };
        }
        return { ...s, [field]: val };
      })
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Workflow name is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit({
        name: name.trim(),
        description: description.trim() || undefined,
        trigger_type: triggerType,
        condition_rules: conditions,
        is_active: isActive,
        steps: steps.map((s) => ({
          step_order: s.step_order,
          name: s.name,
          action_type: s.action_type,
          action_config: s.action_config,
        })),
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create workflow');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-850 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Create Automated Workflow
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Configure event triggers, conditional evaluation, and step actions.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Workflow General Info */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Workflow Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Automated Document Classification & Alert"
                className="w-full text-sm px-3.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                placeholder="Brief summary of what this automation does..."
                className="w-full text-sm px-3.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Event Trigger
                </label>
                <select
                  value={triggerType}
                  onChange={(e) => setTriggerType(e.target.value as WorkflowTriggerType)}
                  className="w-full text-sm px-3.5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="document_created">Document Created</option>
                  <option value="document_updated">Document Updated</option>
                  <option value="security_anomaly">Security Anomaly</option>
                  <option value="connector_synced">Connector Synced</option>
                  <option value="meeting_completed">Meeting Completed</option>
                  <option value="manual">Manual Trigger</option>
                  <option value="scheduled">Scheduled Cron</option>
                </select>
              </div>

              <div className="flex items-center pt-6">
                <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
                  />
                  <span>Activate immediately upon creation</span>
                </label>
              </div>
            </div>
          </div>

          {/* Condition Evaluation Rules */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Condition Rules (Optional)
                </h4>
                <p className="text-xs text-slate-400">
                  Workflow executes only if incoming event matches these predicate conditions.
                </p>
              </div>
              <button
                type="button"
                onClick={handleAddCondition}
                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Rule</span>
              </button>
            </div>

            {conditions.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No conditions set (executes for all events).</p>
            ) : (
              <div className="space-y-2">
                {conditions.map((cond, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={cond.field}
                      onChange={(e) =>
                        handleUpdateCondition(idx, e.target.value, cond.operator, String(cond.value))
                      }
                      placeholder="Field (e.g. classification)"
                      className="flex-1 text-xs px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                    <select
                      value={cond.operator}
                      onChange={(e) =>
                        handleUpdateCondition(
                          idx,
                          cond.field,
                          e.target.value as WorkflowConditionRule['operator'],
                          String(cond.value)
                        )
                      }
                      className="text-xs px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                    >
                      <option value="equals">equals</option>
                      <option value="not_equals">not equals</option>
                      <option value="contains">contains</option>
                      <option value="greater_than">greater than</option>
                      <option value="less_than">less than</option>
                    </select>
                    <input
                      type="text"
                      value={String(cond.value)}
                      onChange={(e) =>
                        handleUpdateCondition(idx, cond.field, cond.operator, e.target.value)
                      }
                      placeholder="Value"
                      className="flex-1 text-xs px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveCondition(idx)}
                      className="p-1 text-slate-400 hover:text-rose-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Ordered Sequence Step Builder */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Execution Steps Pipeline ({steps.length})
                </h4>
                <p className="text-xs text-slate-400">
                  Actions executed in sequential order upon trigger.
                </p>
              </div>
              <button
                type="button"
                onClick={handleAddStep}
                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Step</span>
              </button>
            </div>

            <div className="space-y-3">
              {steps.map((step, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/40 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">
                        {step.step_order}
                      </span>
                      <input
                        type="text"
                        value={step.name}
                        onChange={(e) => handleUpdateStep(idx, 'name', e.target.value)}
                        placeholder="Step Name"
                        className="text-xs font-semibold bg-transparent border-b border-dashed border-slate-300 dark:border-slate-600 focus:outline-none focus:border-indigo-500 text-slate-900 dark:text-white px-1 py-0.5"
                      />
                    </div>
                    {steps.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveStep(idx)}
                        className="p-1 text-slate-400 hover:text-rose-500"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                        Action Type
                      </label>
                      <select
                        value={step.action_type}
                        onChange={(e) => handleUpdateStep(idx, 'action_type', e.target.value)}
                        className="w-full text-xs px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                      >
                        <option value="send_notification">Send Multi-Channel Notification</option>
                        <option value="invoke_llm">Invoke LLM Prompt</option>
                        <option value="request_approval">Request Human Approval</option>
                        <option value="execute_rag_query">Execute RAG Semantic Query</option>
                        <option value="http_webhook">Dispatch HTTP Webhook</option>
                        <option value="trigger_connector_sync">Trigger Connector Sync</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-slate-500 dark:text-slate-400 mb-1">
                        Configuration Summary
                      </label>
                      <div className="text-xs font-mono text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-800 px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-700 truncate">
                        {JSON.stringify(step.action_config)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer Controls */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Creating...' : 'Save & Deploy Workflow'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
