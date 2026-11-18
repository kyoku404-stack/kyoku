import React from 'react';
import { BookOpenCheck, ShieldCheck } from 'lucide-react';
import { useAuthorization } from '@/hooks/useAuthorization';
import { useResearchWorkspace } from '@/hooks/useResearchWorkspace';
import { Permission } from '@/types/permission';
import {
  EvidenceProvenanceDrawer,
  ResearchLaunchForm,
  ResearchReportViewer,
  ResearchRunList,
} from '@/features/research';

export const ResearchAgentsPage: React.FC = () => {
  const { can } = useAuthorization();
  const canInvoke = can(Permission.AGENT_INVOKE);

  const {
    runs,
    statusFilter,
    selectedRunId,
    activeReport,
    evidenceDrawerOpen,
    evidenceItems,
    evidenceRedactedCount,
    highlightedEvidenceId,
    isLoadingRuns,
    isSubmitting,
    isLoadingReport,
    isLoadingEvidence,
    error,
    setStatusFilter,
    refreshRuns,
    launchResearch,
    inspectReport,
    openEvidenceDrawer,
    closeEvidenceDrawer,
    cancelResearch,
  } = useResearchWorkspace();

  const completedCount = runs.filter((r) => r.status === 'completed').length;
  const contradictionTotal = runs.reduce((acc, r) => acc + (r.contradictions?.length ?? 0), 0);
  const insufficientCount = runs.filter((r) => r.status === 'insufficient_evidence').length;

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1.5 flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-800 dark:bg-indigo-950/70 dark:text-indigo-300">
              <BookOpenCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Phase 4.5
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Evidence-First & Citation-Verified
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Research Agents Workspace
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Conduct multi-document internal investigations with traceable citations, contradiction
            detection, and re-authorized evidence provenance.
          </p>
        </div>

        {/* Summary KPI Strip */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[11px] font-medium text-slate-500">Completed</p>
            <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              {completedCount}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[11px] font-medium text-slate-500">Contradictions</p>
            <p className="text-lg font-bold text-amber-600 dark:text-amber-400">
              {contradictionTotal}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-center shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-[11px] font-medium text-slate-500">Insufficient</p>
            <p className="text-lg font-bold text-orange-600 dark:text-orange-400">
              {insufficientCount}
            </p>
          </div>
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-800 dark:bg-rose-950/50 dark:text-rose-200"
        >
          {error}
        </div>
      )}

      {/* Launch Form */}
      <ResearchLaunchForm
        isSubmitting={isSubmitting}
        canInvoke={canInvoke}
        onSubmit={launchResearch}
      />

      {/* Investigation Ledger */}
      <ResearchRunList
        runs={runs}
        statusFilter={statusFilter}
        selectedRunId={selectedRunId}
        isLoading={isLoadingRuns}
        canInvoke={canInvoke}
        onFilterChange={setStatusFilter}
        onRefresh={() => void refreshRuns()}
        onInspectReport={(id) => void inspectReport(id)}
        onInspectEvidence={(id) => void openEvidenceDrawer(id)}
        onCancelRun={(id) => void cancelResearch(id)}
      />

      {/* Structured Citation-Verified Report Viewer */}
      <ResearchReportViewer
        report={activeReport}
        isLoading={isLoadingReport}
        onCitationClick={(researchId, evidenceId) => void openEvidenceDrawer(researchId, evidenceId)}
        onOpenAllEvidence={(researchId) => void openEvidenceDrawer(researchId)}
      />

      {/* Slide-Over Provenance Drawer */}
      <EvidenceProvenanceDrawer
        isOpen={evidenceDrawerOpen}
        isLoading={isLoadingEvidence}
        evidenceItems={evidenceItems}
        redactedCount={evidenceRedactedCount}
        highlightedEvidenceId={highlightedEvidenceId}
        onClose={closeEvidenceDrawer}
      />
    </div>
  );
};
