import React from 'react';
import type { Task, TaskStatus, TaskPriority } from '@/types/task';
import { Card, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckSquare, Clock, AlertTriangle, UserCheck } from 'lucide-react';
import { formatDate } from '@/utils/formatters';

interface TaskListProps {
  tasks: Task[];
  loading?: boolean;
  onToggleStatus?: (task: Task) => void;
}

const getStatusBadge = (status: TaskStatus) => {
  switch (status) {
    case 'DONE':
      return <Badge variant="success">Done</Badge>;
    case 'IN_PROGRESS':
      return <Badge variant="warning">In Progress</Badge>;
    case 'TODO':
      return <Badge variant="secondary">To Do</Badge>;
    case 'CANCELLED':
      return <Badge variant="outline">Cancelled</Badge>;
  }
};

const getPriorityBadge = (priority: TaskPriority) => {
  switch (priority) {
    case 'CRITICAL':
      return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Critical</Badge>;
    case 'HIGH':
      return <Badge variant="warning">High</Badge>;
    case 'MEDIUM':
      return <Badge variant="secondary">Medium</Badge>;
    case 'LOW':
      return <Badge variant="outline">Low</Badge>;
  }
};

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  loading = false,
  onToggleStatus,
}) => {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse h-16 bg-muted/40" />
        ))}
      </div>
    );
  }

  if (!tasks.length) {
    return (
      <Card className="p-8 text-center text-muted-foreground border-dashed">
        <CheckSquare className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="font-medium text-lg text-foreground">No tasks found</p>
        <p className="text-sm mt-1">Tasks linked to projects and user assignments will be listed here.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <Card
          key={task.id}
          className="hover:border-primary/40 transition-all py-2.5 px-4 flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onToggleStatus?.(task)}
              className="p-1 rounded hover:bg-muted text-muted-foreground transition-colors"
              title="Toggle task status"
            >
              <CheckSquare
                className={`w-5 h-5 ${
                  task.status === 'DONE'
                    ? 'text-emerald-500 fill-emerald-500/20'
                    : 'text-muted-foreground'
                }`}
              />
            </button>
            <div>
              <CardTitle className={`text-sm font-medium ${task.status === 'DONE' ? 'line-through text-muted-foreground' : ''}`}>
                {task.title}
              </CardTitle>
              {task.description && (
                <p className="text-xs text-muted-foreground line-clamp-1">{task.description}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {task.due_date && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDate(task.due_date)}
              </span>
            )}
            {task.assignee_id && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <UserCheck className="w-3 h-3" />
                {task.assignee_id.slice(0, 6)}
              </span>
            )}
            {getPriorityBadge(task.priority)}
            {getStatusBadge(task.status)}
          </div>
        </Card>
      ))}
    </div>
  );
};
