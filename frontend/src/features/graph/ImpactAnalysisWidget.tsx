/**
 * KEEP Enterprise Platform — ImpactAnalysisWidget Component (Phase 2.4).
 *
 * Visualizes downstream blast radius, affected departments, dependent projects,
 * impacted operational tasks, and recursive dependency tree.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  AlertTriangle,
  Building2,
  FolderGit2,
  CheckSquare,
  GitBranch,
  X,
  ShieldAlert,
} from 'lucide-react';
import type { ImpactAnalysisResponse } from '@/types/graph';

interface ImpactAnalysisWidgetProps {
  impact: ImpactAnalysisResponse | null;
  onClose: () => void;
  loading?: boolean;
}

export const ImpactAnalysisWidget: React.FC<ImpactAnalysisWidgetProps> = ({
  impact,
  onClose,
  loading = false,
}) => {
  if (!impact) return null;

  const severityScore = impact.severity_score;
  const severityPercentage = Math.round(severityScore * 100);

  // Severity rating
  let severityLabel = 'Low Risk';
  let severityColor = 'bg-emerald-500 text-white';
  if (severityScore >= 0.8) {
    severityLabel = 'Critical Risk';
    severityColor = 'bg-rose-600 text-white';
  } else if (severityScore >= 0.6) {
    severityLabel = 'High Risk';
    severityColor = 'bg-amber-500 text-white';
  } else if (severityScore >= 0.4) {
    severityLabel = 'Moderate Risk';
    severityColor = 'bg-blue-500 text-white';
  }

  return (
    <Card className="flex flex-col border-border bg-card shadow-lg overflow-hidden" data-testid="impact-analysis-widget">
      {/* Header */}
      <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border space-y-0">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-500">
            <ShieldAlert className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-sm font-bold text-foreground flex items-center gap-2">
              Downstream Impact Blast Radius
              {loading && (
                <span className="text-[10px] font-normal text-muted-foreground animate-pulse">Calculating...</span>
              )}
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Evaluating mutations to{' '}
              <span className="font-semibold text-foreground">{impact.root_entity.name}</span> (
              {impact.root_entity.entity_type})
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={onClose}
          data-testid="close-impact-widget"
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Severity Banner */}
        <div className="flex flex-col gap-2 p-3 rounded-lg border border-border bg-muted/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
              Calculated Severity Index
            </span>
            <Badge className={`${severityColor} text-[10px] font-bold px-2 py-0.5`}>
              {severityLabel} ({severityPercentage}%)
            </Badge>
          </div>
          {/* Progress Bar */}
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                severityScore >= 0.8
                  ? 'bg-rose-600'
                  : severityScore >= 0.6
                  ? 'bg-amber-500'
                  : severityScore >= 0.4
                  ? 'bg-blue-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${severityPercentage}%` }}
            />
          </div>
        </div>

        {/* Impact Scope Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Affected Departments */}
          <div className="flex flex-col p-3 rounded-lg border border-border bg-card">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
              <Building2 className="h-4 w-4 text-blue-500" />
              Affected Departments
            </div>
            <div className="mt-1 text-lg font-bold text-foreground">
              {impact.affected_departments.length}
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              {impact.affected_departments.length === 0 ? (
                <span className="text-[11px] text-muted-foreground">None</span>
              ) : (
                impact.affected_departments.map((dept) => (
                  <Badge key={dept} variant="outline" className="text-[10px] px-1.5 py-0">
                    {dept}
                  </Badge>
                ))
              )}
            </div>
          </div>

          {/* Dependent Projects */}
          <div className="flex flex-col p-3 rounded-lg border border-border bg-card">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
              <FolderGit2 className="h-4 w-4 text-purple-500" />
              Dependent Projects
            </div>
            <div className="mt-1 text-lg font-bold text-foreground">
              {impact.dependent_projects.length}
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              {impact.dependent_projects.length === 0 ? (
                <span className="text-[11px] text-muted-foreground">None</span>
              ) : (
                impact.dependent_projects.map((proj) => (
                  <Badge key={proj} variant="outline" className="text-[10px] px-1.5 py-0">
                    {proj}
                  </Badge>
                ))
              )}
            </div>
          </div>

          {/* Impacted Tasks */}
          <div className="flex flex-col p-3 rounded-lg border border-border bg-card">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
              <CheckSquare className="h-4 w-4 text-amber-500" />
              Impacted Tasks
            </div>
            <div className="mt-1 text-lg font-bold text-foreground">
              {impact.impacted_tasks_count}
            </div>
            <span className="text-[11px] text-muted-foreground mt-1">
              Operational deliverables
            </span>
          </div>
        </div>

        {/* Dependency Cascade Tree */}
        <div className="space-y-2">
          <h5 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
            Dependency Propagation Tree ({impact.dependency_tree.length} nodes)
          </h5>
          {impact.dependency_tree.length === 0 ? (
            <p className="text-xs text-muted-foreground italic">No downstream cascade paths identified.</p>
          ) : (
            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {impact.dependency_tree.map((node, i) => (
                <div
                  key={`${node.id}-${i}`}
                  style={{ marginLeft: `${(node.depth - 1) * 16}px` }}
                  className="flex items-center justify-between p-2 rounded-md border border-border bg-card text-xs hover:border-primary/40 transition-all"
                >
                  <div className="flex items-center gap-2 min-w-0 pr-2">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-bold text-muted-foreground">
                      {node.depth}
                    </span>
                    <span className="text-[10px] font-semibold text-purple-600 dark:text-purple-400 uppercase">
                      {node.relation || 'DEPENDS_ON'}
                    </span>
                    <span className="font-medium text-foreground truncate" title={node.name}>
                      {node.name}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-[9px] px-1.5 shrink-0">
                    {node.entity_type}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
