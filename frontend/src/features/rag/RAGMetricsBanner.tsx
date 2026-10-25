/**
 * KEEP Enterprise Platform — RAGMetricsBanner Component (Phase 2.2).
 *
 * Executive KPI stat cards summarizing RAG engine performance, answer
 * latency, semantic confidence scores, user satisfaction, and hallucination guard stats.
 *
 * Specification: devdocs/p2/p2.2.txt Chapter 17 & docs/api/api-contract.md Section 9
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  MessageSquare,
  Clock,
  Sparkles,
  ThumbsUp,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import type { RAGStatistics } from '@/types/rag';

interface RAGMetricsBannerProps {
  statistics: RAGStatistics | null;
  loading?: boolean;
}

export const RAGMetricsBanner: React.FC<RAGMetricsBannerProps> = ({
  statistics,
  loading = false,
}) => {
  const totalQueries = statistics?.total_queries ?? 0;
  const avgLatency = statistics?.average_latency_ms ?? 0;
  const avgConfidence = statistics?.average_confidence_score ?? 0.0;
  const positiveFeedback = statistics?.positive_feedback_percentage ?? 100.0;
  const refusals = statistics?.hallucination_refusal_count ?? 0;
  const cacheHitRatio = statistics?.cache_hit_ratio ?? 0.0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3" data-testid="rag-metrics-banner">
      {/* 1. Total Queries */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Total Queries
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <MessageSquare className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-total-queries">
            {loading ? '—' : totalQueries.toLocaleString()}
          </div>
          <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <Zap className="h-3 w-3" /> {(cacheHitRatio * 100).toFixed(0)}% cache hit
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 2. Mean Response Latency */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Avg Latency
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
            <Clock className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-avg-latency">
              {loading ? '—' : `${avgLatency.toFixed(0)} ms`}
            </div>
            <Badge variant="outline" className="text-[10px] font-mono py-0">
              Target &lt; 500ms
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Hybrid search + rerank</p>
        </CardContent>
      </Card>

      {/* 3. Mean Confidence Score */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Mean Confidence
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500">
            <Sparkles className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-mean-confidence">
              {loading ? '—' : `${(avgConfidence * 100).toFixed(1)}%`}
            </div>
            <span className="text-[10px] text-muted-foreground">min 70% threshold</span>
          </div>
          <div className="mt-1 h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-purple-500 transition-all duration-500 rounded-full"
              style={{ width: `${Math.min(100, Math.max(0, avgConfidence * 100))}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* 4. Positive Feedback Rate */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Satisfaction
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
            <ThumbsUp className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400" data-testid="metric-satisfaction">
            {loading ? '—' : `${positiveFeedback.toFixed(1)}%`}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Helpful rating ratio</p>
        </CardContent>
      </Card>

      {/* 5. Hallucination Refusals */}
      <Card className="border-border bg-card shadow-xs transition-all hover:border-primary/30">
        <CardHeader className="flex flex-row items-center justify-between pb-1 space-y-0">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Guard Refusals
          </CardTitle>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-500">
            <ShieldCheck className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline justify-between">
            <div className="text-xl font-bold tracking-tight text-foreground" data-testid="metric-refusals">
              {loading ? '—' : refusals}
            </div>
            <Badge variant="outline" className="text-[10px] text-emerald-600 dark:text-emerald-400">
              Safe
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Ungrounded queries blocked</p>
        </CardContent>
      </Card>
    </div>
  );
};
