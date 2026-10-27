/**
 * KEEP Enterprise Platform — EntityDetailPanel Component (Phase 2.4).
 *
 * Side inspection drawer displaying entity metadata, in/out degrees,
 * incoming/outgoing directed relationships, and triggering downstream blast radius analysis.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  X,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  Info,
} from 'lucide-react';
import type {
  EntityResponse,
  EntityRelationshipsResponse,
} from '@/types/graph';

interface EntityDetailPanelProps {
  entity: EntityResponse | null;
  relationships: EntityRelationshipsResponse | null;
  onClose: () => void;
  onAnalyzeImpact: (entityId: string) => void;
  onSelectConnectedEntity: (entityId: string) => void;
  loading?: boolean;
}

export const EntityDetailPanel: React.FC<EntityDetailPanelProps> = ({
  entity,
  relationships,
  onClose,
  onAnalyzeImpact,
  onSelectConnectedEntity,
  loading = false,
}) => {
  if (!entity) return null;

  const outgoing = relationships?.outgoing_relationships || [];
  const incoming = relationships?.incoming_relationships || [];

  return (
    <Card className="flex flex-col h-full border-border bg-card shadow-md overflow-hidden" data-testid="entity-detail-panel">
      {/* Header */}
      <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border space-y-0">
        <div className="flex flex-col gap-1 min-w-0 pr-2">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px] font-semibold uppercase tracking-wider">
              {entity.entity_type}
            </Badge>
            <span className="text-[10px] text-muted-foreground truncate font-mono">
              {entity.id.slice(0, 8)}…
            </span>
            {loading && (
              <span className="text-[10px] text-muted-foreground animate-pulse">Updating...</span>
            )}
          </div>
          <CardTitle className="text-base font-bold truncate text-foreground" title={entity.name}>
            {entity.name}
          </CardTitle>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground shrink-0"
          onClick={onClose}
          data-testid="close-detail-panel"
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Degree stats */}
        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col p-2.5 rounded-lg border border-border bg-muted/40">
            <span className="text-[10px] text-muted-foreground font-medium flex items-center gap-1">
              <ArrowLeft className="h-3 w-3 text-blue-500" /> Incoming Edges
            </span>
            <span className="text-lg font-bold text-foreground mt-0.5">{entity.in_degree}</span>
          </div>
          <div className="flex flex-col p-2.5 rounded-lg border border-border bg-muted/40">
            <span className="text-[10px] text-muted-foreground font-medium flex items-center gap-1">
              <ArrowRight className="h-3 w-3 text-purple-500" /> Outgoing Edges
            </span>
            <span className="text-lg font-bold text-foreground mt-0.5">{entity.out_degree}</span>
          </div>
        </div>

        {/* Action: Run Impact Analysis */}
        <Button
          onClick={() => onAnalyzeImpact(entity.id)}
          className="w-full gap-2 text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-xs"
          data-testid="btn-analyze-impact"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          Analyze Impact Blast Radius
        </Button>

        {/* Entity Properties */}
        {entity.properties && Object.keys(entity.properties).length > 0 && (
          <div className="space-y-1.5">
            <h5 className="text-xs font-semibold text-foreground flex items-center gap-1">
              <Info className="h-3 w-3 text-muted-foreground" /> Properties
            </h5>
            <div className="rounded-lg border border-border bg-muted/30 p-2.5 text-[11px] font-mono text-muted-foreground max-h-32 overflow-y-auto space-y-1">
              {Object.entries(entity.properties).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <span className="text-foreground/80 font-medium">{k}:</span>
                  <span className="truncate max-w-[160px] text-right">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Outgoing Directed Relationships */}
        <div className="space-y-2">
          <h5 className="text-xs font-semibold text-foreground flex items-center justify-between">
            <span className="flex items-center gap-1">
              <ArrowRight className="h-3.5 w-3.5 text-purple-500" /> Outgoing Relations ({outgoing.length})
            </span>
          </h5>
          {outgoing.length === 0 ? (
            <p className="text-[11px] text-muted-foreground italic">No outgoing directed links</p>
          ) : (
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {outgoing.map((rel) => (
                <div
                  key={rel.relationship_id}
                  onClick={() => onSelectConnectedEntity(rel.target_entity_id)}
                  className="flex items-center justify-between p-2 rounded-md border border-border bg-card hover:bg-muted/50 cursor-pointer transition-all text-xs"
                >
                  <div className="flex flex-col min-w-0 pr-2">
                    <span className="text-[10px] font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wider">
                      {rel.relation_type}
                    </span>
                    <span className="font-medium text-foreground truncate" title={rel.target_entity_name}>
                      {rel.target_entity_name}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-[9px] px-1 shrink-0">
                    {rel.target_entity_type}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Incoming Directed Relationships */}
        <div className="space-y-2">
          <h5 className="text-xs font-semibold text-foreground flex items-center justify-between">
            <span className="flex items-center gap-1">
              <ArrowLeft className="h-3.5 w-3.5 text-blue-500" /> Incoming Relations ({incoming.length})
            </span>
          </h5>
          {incoming.length === 0 ? (
            <p className="text-[11px] text-muted-foreground italic">No incoming directed links</p>
          ) : (
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {incoming.map((rel) => (
                <div
                  key={rel.relationship_id}
                  onClick={() => onSelectConnectedEntity(rel.source_entity_id)}
                  className="flex items-center justify-between p-2 rounded-md border border-border bg-card hover:bg-muted/50 cursor-pointer transition-all text-xs"
                >
                  <div className="flex flex-col min-w-0 pr-2">
                    <span className="text-[10px] font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                      {rel.relation_type}
                    </span>
                    <span className="font-medium text-foreground truncate" title={rel.source_entity_name}>
                      {rel.source_entity_name}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-[9px] px-1 shrink-0">
                    {rel.source_entity_type}
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
