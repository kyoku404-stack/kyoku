import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useRecentProjects } from '@/hooks/useDashboard';
import { ROUTES } from '@/routes/paths';
import {
  FolderKanban,
  Calendar,
  FileText,
  ArrowRight,
  RefreshCw,
  Users,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const ProjectsWidget: React.FC = () => {
  const { projects, isLoading, error, refresh } = useRecentProjects(6);

  const getPriorityBadge = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return <Badge variant="destructive" className="text-[10px] uppercase font-bold px-1.5 py-0">Critical</Badge>;
      case 'high':
        return <Badge variant="warning" className="text-[10px] uppercase font-bold px-1.5 py-0">High</Badge>;
      case 'medium':
        return <Badge variant="outline" className="text-[10px] uppercase font-bold px-1.5 py-0 text-indigo-500 border-indigo-500/30">Med</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px] uppercase font-bold px-1.5 py-0 text-muted-foreground">Low</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return <Badge variant="success" className="text-[10px] font-semibold">Active</Badge>;
      case 'completed':
        return <Badge variant="outline" className="text-[10px] font-semibold text-emerald-500 border-emerald-500/30">Completed</Badge>;
      case 'on_hold':
        return <Badge variant="outline" className="text-[10px] font-semibold text-amber-500 border-amber-500/30">On Hold</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px] font-semibold text-muted-foreground">{status}</Badge>;
    }
  };

  return (
    <Card className="border border-border bg-card flex flex-col h-full shadow-xs">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
              <FolderKanban className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-foreground">
                Active Projects
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Assigned initiative workspaces
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              onClick={refresh}
              disabled={isLoading}
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              aria-label="Refresh recent projects"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>

            <Link to={ROUTES.PROJECTS}>
              <Button variant="ghost" size="sm" className="h-7 text-xs gap-1 text-primary hover:text-primary">
                <span>View All</span>
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-y-auto max-h-[420px]">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-3 border border-border/60 rounded-xl space-y-2 animate-pulse">
                <div className="flex justify-between items-center">
                  <div className="h-4 w-32 bg-muted rounded" />
                  <div className="h-4 w-12 bg-muted rounded" />
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full" />
              </div>
            ))}
          </div>
        ) : error && projects.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <p>{error}</p>
            <Button size="sm" variant="outline" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : projects.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <FolderKanban className="h-8 w-8 mx-auto text-muted-foreground/40 mb-1" />
            <p>No active projects assigned.</p>
            <Link to={ROUTES.PROJECTS}>
              <Button size="sm" variant="outline" className="mt-2 text-xs">
                Explore Workspaces
              </Button>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-border/60">
            {projects.map((project) => (
              <div
                key={project.id}
                className="p-3.5 hover:bg-muted/30 transition-colors space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 space-y-0.5">
                    <Link
                      to={ROUTES.PROJECTS}
                      className="text-xs font-semibold text-foreground hover:text-primary transition-colors block truncate"
                    >
                      {project.name}
                    </Link>
                    {project.description && (
                      <p className="text-[11px] text-muted-foreground truncate">
                        {project.description}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {getPriorityBadge(project.priority)}
                    {getStatusBadge(project.status)}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span>Progress</span>
                    <span className="font-semibold text-foreground">
                      {project.progress_percent}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                      style={{ width: `${project.progress_percent}%` }}
                    />
                  </div>
                </div>

                {/* Metadata footer */}
                <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-0.5">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      <span>{project.document_count} docs</span>
                    </span>

                    {project.team_members && project.team_members.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        <span>{project.team_members.length} members</span>
                      </span>
                    )}
                  </div>

                  {project.deadline && (
                    <span className="flex items-center gap-1 text-[10px]">
                      <Calendar className="h-3 w-3 text-muted-foreground" />
                      <span>Due {formatDate(project.deadline)}</span>
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
