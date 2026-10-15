import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useActivityFeed } from '@/hooks/useDashboard';
import {
  Activity,
  Filter,
  FileText,
  FolderKanban,
  Video,
  User,
  Sparkles,
  Clock,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const ActivityFeedWidget: React.FC = () => {
  const {
    events,
    filter,
    page,
    totalPages,
    total,
    isLoading,
    error,
    changeFilter,
    setPage,
    refresh,
  } = useActivityFeed('all');

  const getActionIcon = (resourceType: string) => {
    switch (resourceType?.toLowerCase()) {
      case 'document':
        return <FileText className="h-4 w-4 text-emerald-500" />;
      case 'project':
        return <FolderKanban className="h-4 w-4 text-indigo-500" />;
      case 'meeting':
        return <Video className="h-4 w-4 text-blue-500" />;
      case 'ai_summary':
      case 'ai':
        return <Sparkles className="h-4 w-4 text-purple-500" />;
      default:
        return <User className="h-4 w-4 text-amber-500" />;
    }
  };

  return (
    <Card className="border border-border bg-card flex flex-col h-full shadow-xs">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-foreground">
                Recent Activity
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Live organizational event stream ({total} total)
              </CardDescription>
            </div>
          </div>

          {/* Filter dropdown */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Filter className="h-3.5 w-3.5" />
              <select
                value={filter}
                onChange={(e) => changeFilter(e.target.value)}
                className="h-7 rounded-md border border-border bg-background px-2 text-xs text-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
                aria-label="Filter activity by resource type"
              >
                <option value="all">All Events</option>
                <option value="document">Documents</option>
                <option value="project">Projects</option>
                <option value="meeting">Meetings</option>
                <option value="user">Users</option>
              </select>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={refresh}
              disabled={isLoading}
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              aria-label="Refresh activity feed"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-y-auto max-h-[420px]">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-start gap-3 animate-pulse">
                <div className="h-8 w-8 rounded-full bg-muted shrink-0" />
                <div className="space-y-1.5 flex-1">
                  <div className="h-3.5 w-3/4 bg-muted rounded" />
                  <div className="h-3 w-1/3 bg-muted rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : error && events.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <p>{error}</p>
            <Button size="sm" variant="outline" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            No recent activity recorded for this filter.
          </div>
        ) : (
          <div className="divide-y divide-border/60">
            {events.map((event) => (
              <div
                key={event.id}
                className="flex items-start gap-3 p-3.5 hover:bg-muted/30 transition-colors"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted/60 shrink-0 mt-0.5 border border-border/40">
                  {getActionIcon(event.resource_type)}
                </div>

                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap text-xs">
                    <span className="font-semibold text-foreground">
                      {event.actor?.full_name || 'System'}
                    </span>
                    <span className="text-muted-foreground text-[11px]">
                      {event.action}
                    </span>
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-border text-foreground font-medium truncate max-w-[180px]">
                      {event.resource_name}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>{formatDate(event.occurred_at)}</span>
                    <span className="capitalize">• {event.resource_type}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-border px-3.5 py-2.5 bg-muted/20 text-xs">
          <span className="text-muted-foreground text-[11px]">
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="h-7 text-xs px-2"
            >
              <ChevronLeft className="h-3 w-3 mr-0.5" />
              Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="h-7 text-xs px-2"
            >
              Next
              <ChevronRight className="h-3 w-3 ml-0.5" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};
