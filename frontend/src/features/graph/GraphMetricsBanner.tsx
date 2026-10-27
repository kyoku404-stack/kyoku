/**
 * KEEP Enterprise Platform — GraphMetricsBanner Component (Phase 2.4).
 *
 * Displays executive graph topology KPIs: Total Entities, Active Relationships,
 * Topological Density, Top Hub Node, and Graph Extraction Velocity.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Share2,
  Activity,
  Layers,
  Crown,
} from 'lucide-react';
import type { GraphMetricsResponse } from '@/types/graph';

interface GraphMetricsBannerProps {
  metrics: GraphMetricsResponse | null;
  loading?: boolean;
}

export const GraphMetricsBanner: React.FC<GraphMetricsBannerProps> = ({
  metrics,
  loading = false,
}) => {
  const totalEntities = metrics?.total_entities ?? 0;
  const totalRelationships = metrics?.total_relationships ?? 0;
  const density = metrics?.density ?? 0.0;
  const topHub = metrics?.top_hub || 'None';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="graph-metrics-banner">
      {/* 1. Total Entities */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Total Entities
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500">
            <Layers className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-total-entities">
            {loading ? '—' : totalEntities.toLocaleString()}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="text-emerald-600 dark:text-emerald-400 font-medium">Nodes indexed</span>
          </div>
        </CardContent>
      </Card>

      {/* 2. Total Relationships */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Active Relationships
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500">
            <Share2 className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-total-relationships">
            {loading ? '—' : totalRelationships.toLocaleString()}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <span>Directed semantic triples</span>
          </div>
        </CardContent>
      </Card>

      {/* 3. Graph Density */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Network Density
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
            <Activity className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-density">
            {loading ? '—' : (density * 100).toFixed(2) + '%'}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <span>Topological connectivity</span>
          </div>
        </CardContent>
      </Card>

      {/* 4. Top Hub Node */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Top Central Hub
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
            <Crown className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-base font-bold tracking-tight truncate text-foreground" title={topHub} data-testid="metric-top-hub">
            {loading ? '—' : topHub}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Badge variant="outline" className="text-[10px] px-1.5 py-0">
              Highest degree
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
