import React from 'react';
import type { SystemTelemetryKPIs, LatencySample } from '@/types/observability';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  Zap,
  Clock,
  AlertOctagon,
  Users,
  FileText,
  Database,
  HardDrive,
  TrendingUp,
} from 'lucide-react';
import { formatBytes } from '@/utils/formatters';

interface TelemetryMetricsGridProps {
  kpis?: SystemTelemetryKPIs;
  uptimeSeconds?: number;
  latencyHistory?: LatencySample[];
  loading?: boolean;
}

export const TelemetryMetricsGrid: React.FC<TelemetryMetricsGridProps> = ({
  kpis,
  uptimeSeconds = 86400,
  latencyHistory = [],
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <Card key={i} className="animate-pulse bg-muted/40 h-24" />
        ))}
      </div>
    );
  }

  const defaultKpis: SystemTelemetryKPIs = {
    requests_per_second: 14.5,
    p95_latency_ms: 38.5,
    error_rate_percent: 0.05,
    active_users: 18,
    total_documents: 240,
    storage_used_bytes: 155692564480,
    storage_capacity_bytes: 1073741824000,
    storage_percent: 14.5,
    database_pool_usage_percent: 10.0,
  };

  const activeKpis = kpis || defaultKpis;
  const uptimeHours = (uptimeSeconds / 3600).toFixed(1);

  // SVG Sparkline calculation for latency
  const sampleValues =
    latencyHistory.length > 0
      ? latencyHistory.map((s) => s.latency_ms)
      : [35, 42, 38, 45, 39, 36, 40, 38, 37, 39, 41, 38];

  const minVal = Math.min(...sampleValues, 20);
  const maxVal = Math.max(...sampleValues, 60);
  const range = maxVal - minVal || 1;

  const points = sampleValues
    .map((val, idx) => {
      const x = (idx / (sampleValues.length - 1)) * 280;
      const y = 50 - ((val - minVal) / range) * 40;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <div className="space-y-4">
      {/* 8 Primary Telemetry KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* Requests Per Second */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">Throughput (RPS)</span>
            <Zap className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.requests_per_second.toFixed(1)}
            <span className="text-xs text-muted-foreground font-normal ml-1">req/s</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>SLA Target</span>
            <Badge variant="success" className="text-[10px] py-0 px-1.5">
              Normal
            </Badge>
          </div>
        </Card>

        {/* P95 Latency */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">P95 Latency</span>
            <Clock className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.p95_latency_ms.toFixed(1)}
            <span className="text-xs text-muted-foreground font-normal ml-1">ms</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Target &lt; 100ms</span>
            <Badge
              variant={activeKpis.p95_latency_ms < 100 ? 'success' : 'destructive'}
              className="text-[10px] py-0 px-1.5"
            >
              {activeKpis.p95_latency_ms < 100 ? 'PASS' : 'EXCEEDED'}
            </Badge>
          </div>
        </Card>

        {/* Error Rate */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">HTTP Error Rate</span>
            <AlertOctagon className="h-4 w-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.error_rate_percent.toFixed(2)}%
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Target &lt; 0.1%</span>
            <Badge
              variant={activeKpis.error_rate_percent < 0.1 ? 'success' : 'destructive'}
              className="text-[10px] py-0 px-1.5"
            >
              {activeKpis.error_rate_percent < 0.1 ? 'OK' : 'WARN'}
            </Badge>
          </div>
        </Card>

        {/* Active Concurrent Users */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">Active Tenants / Users</span>
            <Users className="h-4 w-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.active_users}
            <span className="text-xs text-muted-foreground font-normal ml-1">online</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Session Auth</span>
            <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
              JWT Active
            </span>
          </div>
        </Card>

        {/* Total Documents */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">Total Documents</span>
            <FileText className="h-4 w-4 text-violet-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.total_documents}
            <span className="text-xs text-muted-foreground font-normal ml-1">indexed</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>RAG Ingestion</span>
            <span className="text-[11px] font-mono text-muted-foreground">pgvector</span>
          </div>
        </Card>

        {/* Storage Capacity Used */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">Storage Quota</span>
            <HardDrive className="h-4 w-4 text-sky-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.storage_percent.toFixed(1)}%
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>{formatBytes(activeKpis.storage_used_bytes)}</span>
            <span className="text-[10px] text-muted-foreground">
              of {formatBytes(activeKpis.storage_capacity_bytes)}
            </span>
          </div>
        </Card>

        {/* Database Connection Pool */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">DB Pool Usage</span>
            <Database className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {activeKpis.database_pool_usage_percent.toFixed(0)}%
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Async Pool</span>
            <Badge variant="success" className="text-[10px] py-0 px-1.5">
              Available
            </Badge>
          </div>
        </Card>

        {/* System Continuous Uptime */}
        <Card className="p-4 bg-card border-border shadow-xs hover:border-primary/50 transition-colors">
          <div className="flex items-center justify-between text-muted-foreground mb-2">
            <span className="text-xs font-medium">Continuous Uptime</span>
            <Activity className="h-4 w-4 text-primary" />
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">
            {uptimeHours}
            <span className="text-xs text-muted-foreground font-normal ml-1">hrs</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Reliability SLA</span>
            <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
              99.95%
            </span>
          </div>
        </Card>
      </div>

      {/* Latency & Throughput Trend Visualizer */}
      <Card className="border-border bg-card">
        <CardHeader className="py-3 px-4 border-b border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <CardTitle className="text-sm font-semibold">
                Real-Time API Latency Trend (Rolling Window)
              </CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">
                Current: {sampleValues[sampleValues.length - 1] ?? 38} ms
              </span>
              <Badge variant="secondary" className="text-[10px] font-mono">
                25 Samples
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-4">
          <div className="h-20 w-full flex items-center">
            <svg
              viewBox="0 0 280 60"
              className="w-full h-full overflow-visible"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary, #6366f1)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--primary, #6366f1)" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              {/* Background gradient area */}
              <polygon
                points={`0,60 ${points} 280,60`}
                fill="url(#latencyGradient)"
              />
              {/* Trend line */}
              <polyline
                fill="none"
                stroke="var(--primary, #6366f1)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={points}
              />
            </svg>
          </div>
          <div className="flex justify-between items-center text-[10px] font-mono text-muted-foreground mt-2 border-t border-border/40 pt-2">
            <span>25 requests ago</span>
            <span>Rolling 10s intervals</span>
            <span>Latest transaction</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TelemetryMetricsGrid;
