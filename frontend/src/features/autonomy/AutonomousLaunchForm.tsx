import React, { useState } from 'react';
import { Play, ShieldAlert, Sparkles } from 'lucide-react';
import type { AutonomousWorkflowRequest } from '@/types/autonomy';

interface AutonomousLaunchFormProps {
  isSubmitting: boolean;
  canInvoke: boolean;
  onSubmit: (payload: AutonomousWorkflowRequest) => Promise<void>;
}

const WORKFLOW_OPTIONS = [
  { value: 'churn_investigation', label: 'Churn Investigation (Adaptive)' },
  { value: 'autonomous_research', label: 'Autonomous Research' },
  { value: 'autonomous_investigation', label: 'Deep Enterprise Investigation' },
  { value: 'autonomous_collaboration', label: 'Multi-Agent Autonomous Collaboration' },
  { value: 'knowledge_analysis', label: 'Knowledge Analysis' },
];

export const AutonomousLaunchForm: React.FC<AutonomousLaunchFormProps> = ({
  isSubmitting,
  canInvoke,
  onSubmit,
}) => {
  const [objective, setObjective] = useState('');
  const [workflowId, setWorkflowId] = useState('churn_investigation');
  const [maxSteps, setMaxSteps] = useState(12);
  const [maxReplans, setMaxReplans] = useState(2);
  const [maxAgentAttempts, setMaxAgentAttempts] = useState(2);
  const [deadlineSeconds, setDeadlineSeconds] = useState(600);
  const [requireApprovalForWrites, setRequireApprovalForWrites] = useState(true);

  const loadChurnDemo = () => {
    setWorkflowId('churn_investigation');
    setObjective(
      'Investigate the sudden Q4 rise in enterprise customer churn, analyze support escalations, and recommend retention actions.'
    );
    setMaxSteps(12);
    setMaxReplans(2);
    setRequireApprovalForWrites(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!objective.trim() || !canInvoke || isSubmitting) return;
    await onSubmit({
      objective: objective.trim(),
      workflow_id: workflowId,
      mode: 'sync',
      policy: {
        max_steps: maxSteps,
        max_replans: maxReplans,
        max_agent_attempts: maxAgentAttempts,
        deadline_seconds: deadlineSeconds,
        require_approval_for_writes: requireApprovalForWrites,
      },
    });
  };

  return (
    <section
      aria-labelledby="autonomy-launch-heading"
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2
            id="autonomy-launch-heading"
            className="text-base font-semibold text-slate-900 dark:text-slate-100"
          >
            Launch Goal-Driven Workflow
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Specify an enterprise objective and bounded autonomy policy limits.
          </p>
        </div>
        <button
          type="button"
          onClick={loadChurnDemo}
          className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-900/60 dark:bg-indigo-950/50 dark:text-indigo-300"
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Load Churn Investigation Demo
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="autonomy-objective-input"
            className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
          >
            Workflow Objective
          </label>
          <textarea
            id="autonomy-objective-input"
            rows={3}
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="e.g., Investigate why customer churn spiked last month and draft retention recommendations..."
            required
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-xs focus:border-indigo-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div className="sm:col-span-2 lg:col-span-2">
            <label
              htmlFor="autonomy-workflow-type"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Workflow Archetype
            </label>
            <select
              id="autonomy-workflow-type"
              value={workflowId}
              onChange={(e) => setWorkflowId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            >
              {WORKFLOW_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="autonomy-max-steps"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Max Steps
            </label>
            <input
              id="autonomy-max-steps"
              type="number"
              min={1}
              max={25}
              value={maxSteps}
              onChange={(e) => setMaxSteps(Number(e.target.value) || 1)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>

          <div>
            <label
              htmlFor="autonomy-max-replans"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Max Replans
            </label>
            <input
              id="autonomy-max-replans"
              type="number"
              min={0}
              max={3}
              value={maxReplans}
              onChange={(e) => setMaxReplans(Number(e.target.value) || 0)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>

          <div>
            <label
              htmlFor="autonomy-deadline"
              className="mb-1 block text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              Deadline (s)
            </label>
            <input
              id="autonomy-deadline"
              type="number"
              min={10}
              max={1800}
              value={deadlineSeconds}
              onChange={(e) => setDeadlineSeconds(Number(e.target.value) || 60)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 dark:border-slate-800">
          <div className="flex flex-wrap items-center gap-4">
            <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={requireApprovalForWrites}
                onChange={(e) => setRequireApprovalForWrites(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span>Require human approval before write operations</span>
            </label>
            <label className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
              <span>Retries/step:</span>
              <input
                aria-label="Max agent attempts"
                type="number"
                min={1}
                max={3}
                value={maxAgentAttempts}
                onChange={(e) => setMaxAgentAttempts(Number(e.target.value) || 1)}
                className="w-14 rounded border border-slate-300 px-1.5 py-0.5 text-xs dark:border-slate-700 dark:bg-slate-950"
              />
            </label>
          </div>

          {!canInvoke ? (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 dark:text-amber-400">
              <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />
              Requires agent.invoke permission
            </span>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting || !objective.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-xs transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Play className="h-4 w-4" aria-hidden="true" />
              {isSubmitting ? 'Executing Autonomous Loop...' : 'Start Autonomous Workflow'}
            </button>
          )}
        </div>
      </form>
    </section>
  );
};
