import React from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import type {
  AutonomousStepRecord,
  AutonomousWorkflowRecord,
  AutonomyTimelineResponse,
} from '@/types/autonomy';

interface AutonomousWorkflowInspectorProps {
  workflow: AutonomousWorkflowRecord | null;
  steps: AutonomousStepRecord[];
  timeline: AutonomyTimelineResponse | null;
  canInvoke: boolean;
  isUpdatingAction: boolean;
  onResume: (executionId: string, approve: boolean, reason: string) => Promise<void>;
  onCancel: (executionId: string, reason: string) => Promise<void>;
}

export const AutonomousWorkflowInspector: React.FC<AutonomousWorkflowInspectorProps> = ({
  workflow,
  steps,
  timeline,
  canInvoke,
  isUpdatingAction,
  onResume,
  onCancel,
}) => {
  if (!workflow) {
    return (
      <section
        aria-label="Workflow Inspector"
        className="flex min-h-64 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white p-8 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900"
      >
        Select an autonomous workflow execution to inspect planned steps, decisions, and outcomes.
      </section>
    );
  }

  const budget = workflow.budget;
  const isTerminal = ['completed', 'failed', 'budget_exhausted', 'cancelled'].includes(
    workflow.status
  );
  const findings = workflow.final_result?.findings ?? [];
  const evidenceRefs = workflow.final_result?.evidence_refs ?? [];
  const limitations =
    workflow.limitations?.length > 0
      ? workflow.limitations
      : (workflow.final_result?.limitations ?? []);

  return (
    <section
      aria-labelledby="autonomy-inspector-heading"
      className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900"
    >
      {/* Top Header & Actions */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">
              {workflow.execution_id}
            </span>
            <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
              {workflow.status}
            </span>
          </div>
          <h2
            id="autonomy-inspector-heading"
            className="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100"
          >
            {workflow.objective}
          </h2>
          {workflow.termination_reason && (
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
              Outcome Reason: <span className="font-medium">{workflow.termination_reason}</span>
            </p>
          )}
        </div>

        {canInvoke && !isTerminal && workflow.status !== 'awaiting_approval' && (
          <button
            type="button"
            disabled={isUpdatingAction}
            onClick={() => onCancel(workflow.execution_id, 'Cancelled from Autonomous Console')}
            className="inline-flex items-center gap-1.5 rounded-lg border border-rose-300 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
          >
            <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
            Cancel Workflow
          </button>
        )}
      </div>

      {/* Approval Gate Banner */}
      {workflow.status === 'awaiting_approval' && (
        <div
          role="alert"
          className="rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800/60 dark:bg-amber-950/30"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-600" aria-hidden="true" />
              <div>
                <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
                  Human Approval Required Before Side-Effecting Write
                </p>
                <p className="text-xs text-amber-800 dark:text-amber-300">
                  Execution paused safely without executing unapproved external writes. Revalidate
                  and approve to continue from checkpoint.
                </p>
              </div>
            </div>
            {canInvoke && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={isUpdatingAction}
                  onClick={() =>
                    onResume(
                      workflow.execution_id,
                      true,
                      'Approved write operation via Autonomous Console'
                    )
                  }
                  className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                  Approve & Resume
                </button>
                <button
                  type="button"
                  disabled={isUpdatingAction}
                  onClick={() =>
                    onCancel(workflow.execution_id, 'Write approval declined by operator')
                  }
                  className="inline-flex items-center gap-1 rounded-lg border border-rose-300 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                >
                  Reject & Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Budget & Telemetry Row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
          <p className="text-[11px] font-medium text-slate-500">Step Budget</p>
          <p className="mt-0.5 text-sm font-bold text-slate-900 dark:text-slate-100">
            {budget?.steps_consumed ?? workflow.current_step_index} / {workflow.policy.max_steps}
          </p>
        </div>
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
          <p className="text-[11px] font-medium text-slate-500">Bounded Replans</p>
          <p className="mt-0.5 text-sm font-bold text-slate-900 dark:text-slate-100">
            {budget?.replans_consumed ?? workflow.replan_count} / {workflow.policy.max_replans}
          </p>
        </div>
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
          <p className="text-[11px] font-medium text-slate-500">Agent Attempts</p>
          <p className="mt-0.5 text-sm font-bold text-slate-900 dark:text-slate-100">
            {budget?.total_agent_attempts ?? 0} (cap {workflow.policy.max_agent_attempts}/step)
          </p>
        </div>
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
          <p className="text-[11px] font-medium text-slate-500">Write Gating</p>
          <p className="mt-0.5 flex items-center gap-1 text-sm font-bold text-slate-900 dark:text-slate-100">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
            {workflow.policy.require_approval_for_writes ? 'Enforced' : 'Permissive'}
          </p>
        </div>
      </div>

      {/* Step Execution History */}
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Executed & Planned Steps ({steps.length})
        </h3>
        <div className="space-y-2">
          {steps.map((step) => (
            <div
              key={step.step_id}
              className="rounded-lg border border-slate-200 p-3 text-xs dark:border-slate-800"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] font-semibold text-slate-500">
                    #{step.step_order} (v{step.plan_version})
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                    {step.title}
                  </span>
                  {step.is_side_effecting && (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-800">
                      Write Action
                    </span>
                  )}
                </div>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  {step.status}
                </span>
              </div>
              <div className="mt-1 flex flex-wrap gap-3 text-[11px] text-slate-500">
                <span>Agent: {step.agent_id}</span>
                <span>
                  Attempt: {step.attempt}/{step.max_attempts}
                </span>
                {typeof step.outputs?.summary === 'string' && (
                  <span className="text-slate-700 dark:text-slate-300">
                    Output: {step.outputs.summary}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Decisions & Events */}
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Controller Decisions & Audit Trail
        </h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <p className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
              Decisions ({timeline?.decisions?.length ?? 0})
            </p>
            <ul className="space-y-1.5 text-xs">
              {(timeline?.decisions ?? []).map((dec) => (
                <li key={dec.decision_id} className="rounded bg-slate-50 p-2 dark:bg-slate-950">
                  <span className="font-mono text-[11px] font-semibold text-indigo-600">
                    {dec.action}
                  </span>
                  <p className="text-slate-700 dark:text-slate-300">{dec.reason}</p>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <p className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
              Lifecycle Events ({timeline?.events?.length ?? 0})
            </p>
            <ul className="space-y-1.5 text-xs">
              {(timeline?.events ?? []).map((evt) => (
                <li
                  key={evt.event_id}
                  className="flex items-start gap-2 rounded bg-slate-50 p-2 dark:bg-slate-950"
                >
                  <Clock className="mt-0.5 h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
                  <div>
                    <span className="font-mono text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                      {evt.event_type}
                    </span>
                    <p className="text-[11px] text-slate-500">Actor: {evt.actor_id}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Final Report & Limitations */}
      {(findings.length > 0 || limitations.length > 0 || evidenceRefs.length > 0) && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50/40 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-emerald-800 dark:text-emerald-300">
            Final Synthesis & Limitations
          </h3>
          {workflow.final_result?.summary && (
            <p className="mt-1 text-xs text-slate-800 dark:text-slate-200">
              {workflow.final_result.summary}
            </p>
          )}
          {evidenceRefs.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {evidenceRefs.map((ref) => (
                <span
                  key={ref}
                  className="rounded bg-white px-2 py-0.5 font-mono text-[11px] text-indigo-700 shadow-2xs dark:bg-slate-900 dark:text-indigo-300"
                >
                  {ref}
                </span>
              ))}
            </div>
          )}
          {limitations.length > 0 && (
            <div className="mt-3 border-t border-emerald-200/70 pt-2">
              <p className="text-[11px] font-semibold text-amber-800 dark:text-amber-300">
                Stated Limitations:
              </p>
              <ul className="mt-1 list-disc pl-4 text-xs text-slate-700 dark:text-slate-300">
                {limitations.map((lim, i) => (
                  <li key={`${lim}-${i}`}>{lim}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
