import React from 'react';
import type { Project, ProjectStatus, ProjectPriority } from '@/types/project';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FolderGit2, Calendar, FileText, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { formatDate } from '@/utils/formatters';

interface ProjectListProps {
  projects: Project[];
  loading?: boolean;
  onSelectProject?: (project: Project) => void;
}

const getStatusBadge = (status: ProjectStatus) => {
  switch (status) {
    case 'ACTIVE':
      return <Badge variant="success" className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Active</Badge>;
    case 'ARCHIVED':
      return <Badge variant="secondary" className="flex items-center gap-1"><Clock className="w-3 h-3" /> Archived</Badge>;
    case 'COMPLETED':
      return <Badge variant="outline" className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Completed</Badge>;
    default:
      return <Badge variant="default">{status}</Badge>;
  }
};

const getPriorityBadge = (priority: ProjectPriority) => {
  switch (priority) {
    case 'CRITICAL':
      return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Critical</Badge>;
    case 'HIGH':
      return <Badge variant="warning">High</Badge>;
    case 'MEDIUM':
      return <Badge variant="secondary">Medium</Badge>;
    case 'LOW':
      return <Badge variant="outline">Low</Badge>;
    default:
      return <Badge variant="default">{priority}</Badge>;
  }
};

export const ProjectList: React.FC<ProjectListProps> = ({
  projects,
  loading = false,
  onSelectProject,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse h-48 bg-muted/40" />
        ))}
      </div>
    );
  }

  if (!projects.length) {
    return (
      <Card className="p-8 text-center text-muted-foreground border-dashed">
        <FolderGit2 className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="font-medium text-lg text-foreground">No projects found</p>
        <p className="text-sm mt-1">Create your first enterprise project workspace to begin indexing knowledge.</p>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <Card
          key={project.id}
          className="hover:border-primary/50 transition-all cursor-pointer group flex flex-col justify-between"
          onClick={() => onSelectProject?.(project)}
        >
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                  <FolderGit2 className="w-5 h-5" />
                </div>
                <div>
                  <CardTitle className="text-base font-semibold line-clamp-1">{project.name}</CardTitle>
                  <CardDescription className="text-xs">ID: {project.id.slice(0, 8)}...</CardDescription>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                {getStatusBadge(project.status)}
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2 text-sm text-muted-foreground flex-1 flex flex-col justify-between">
            <p className="line-clamp-2 mb-4 text-xs font-normal">
              {project.description || 'No description provided for this workspace.'}
            </p>

            <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  {project.document_count ?? 0} docs
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {formatDate(project.created_at)}
                </span>
              </div>
              {getPriorityBadge(project.priority)}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
