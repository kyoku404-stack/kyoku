import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAnalyticsSummary } from '@/hooks/useDashboard';
import {
  BarChart3,
  RefreshCw,
  Users,
  FileText,
  PieChart,
} from 'lucide-react';

export const AnalyticsWidget: React.FC = () => {
  const { analytics, period, setPeriod, isLoading, error, refresh } =
    useAnalyticsSummary('week');

  const maxUploaded = Math.max(
    1,
    ...(analytics?.documents_uploaded.map((p) => p.value) || [1])
  );
  const maxActive = Math.max(
    1,
    ...(analytics?.active_users.map((p) => p.value) || [1])
  );

  return (
    <Card className="border border-border bg-card flex flex-col h-full shadow-xs">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-pink-500/10 text-pink-500">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-foreground">
                  Organizational Analytics
                </CardTitle>
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-pink-500/30 text-pink-500 bg-pink-500/5">
                  Admin Exclusive
                </Badge>
              </div>
              <CardDescription className="text-xs text-muted-foreground">
                Knowledge adoption, user activity & project progression
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Period switcher */}
            <div className="flex rounded-lg border border-border p-0.5 bg-muted/40 text-xs">
              {(['week', 'month', 'quarter', 'year'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium capitalize transition-all ${
                    period === p
                      ? 'bg-background text-foreground font-semibold shadow-2xs'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={refresh}
              disabled={isLoading}
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              aria-label="Refresh analytics"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-6">
        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="space-y-3 w-full animate-pulse">
              <div className="h-4 bg-muted rounded w-1/4" />
              <div className="h-28 bg-muted rounded-xl" />
              <div className="h-4 bg-muted rounded w-1/3" />
              <div className="h-20 bg-muted rounded-xl" />
            </div>
          </div>
        ) : error && !analytics ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <p>{error}</p>
            <Button size="sm" variant="outline" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : !analytics ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            No analytics data available for this timeframe.
          </div>
        ) : (
          <div className="space-y-5">
            {/* 1. Documents Uploaded Time Series */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-emerald-500" />
                  <span>Documents Ingestion Trend</span>
                </span>
                <span className="text-[11px] text-muted-foreground">
                  Period: <span className="capitalize font-medium text-foreground">{period}</span>
                </span>
              </div>

              <div className="h-24 flex items-end gap-2 pt-2 border-b border-border/50 pb-1">
                {analytics.documents_uploaded && analytics.documents_uploaded.length > 0 ? (
                  analytics.documents_uploaded.map((pt, idx) => {
                    const heightPercent = Math.max(8, Math.round((pt.value / maxUploaded) * 100));
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                        {/* Hover tooltip */}
                        <div className="absolute -top-7 hidden group-hover:flex px-1.5 py-0.5 rounded bg-popover text-popover-foreground text-[10px] font-semibold shadow-xs border border-border whitespace-nowrap z-20">
                          {pt.label}: {pt.value} docs
                        </div>
                        <div
                          className="w-full bg-emerald-500/80 hover:bg-emerald-500 rounded-t-sm transition-all duration-300"
                          style={{ height: `${heightPercent}%` }}
                        />
                        <span className="text-[10px] text-muted-foreground truncate max-w-full">
                          {pt.label}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div className="w-full text-center text-xs text-muted-foreground py-6">
                    No upload events recorded
                  </div>
                )}
              </div>
            </div>

            {/* 2. Active Users Time Series */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5 text-blue-500" />
                  <span>Active Knowledge Seekers</span>
                </span>
                <span className="text-[11px] text-muted-foreground">User Traffic</span>
              </div>

              <div className="h-20 flex items-end gap-2 pt-2 border-b border-border/50 pb-1">
                {analytics.active_users && analytics.active_users.length > 0 ? (
                  analytics.active_users.map((pt, idx) => {
                    const heightPercent = Math.max(8, Math.round((pt.value / maxActive) * 100));
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                        <div className="absolute -top-7 hidden group-hover:flex px-1.5 py-0.5 rounded bg-popover text-popover-foreground text-[10px] font-semibold shadow-xs border border-border whitespace-nowrap z-20">
                          {pt.label}: {pt.value} users
                        </div>
                        <div
                          className="w-full bg-blue-500/80 hover:bg-blue-500 rounded-t-sm transition-all duration-300"
                          style={{ height: `${heightPercent}%` }}
                        />
                        <span className="text-[10px] text-muted-foreground truncate max-w-full">
                          {pt.label}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div className="w-full text-center text-xs text-muted-foreground py-4">
                    No user session telemetry recorded
                  </div>
                )}
              </div>
            </div>

            {/* 3. Project Status Distribution */}
            {analytics.project_distribution && analytics.project_distribution.length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-foreground flex items-center gap-1.5">
                    <PieChart className="h-3.5 w-3.5 text-indigo-500" />
                    <span>Project Status Distribution</span>
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {analytics.project_distribution.map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-border/60 bg-muted/20 p-2 text-center"
                    >
                      <div className="text-base font-bold text-foreground">
                        {item.count}
                      </div>
                      <div className="text-[10px] text-muted-foreground uppercase font-medium tracking-wider">
                        {item.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
