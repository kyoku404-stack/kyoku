import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ProjectList } from '@/features/projects/ProjectList';
import { MeetingList } from '@/features/meetings/MeetingList';
import { TaskList } from '@/features/tasks/TaskList';
import { KnowledgeGraphView } from '@/features/knowledge/KnowledgeGraphView';
import { ActivityLogTable } from '@/features/activity/ActivityLogTable';
import type { Project } from '@/types/project';
import type { Meeting } from '@/types/meeting';
import type { Task } from '@/types/task';
import type { KgEntity, KgRelationship } from '@/types/knowledge';
import type { ActivityLog } from '@/types/activity';
import {
  FileText,
  Cpu,
  Database,
  Users,
  FolderGit2,
  Video,
  CheckSquare,
  Network,
  Activity,
  ArrowUpRight,
} from 'lucide-react';

const MOCK_PROJECTS: Project[] = [
  {
    id: 'proj-1111-2222-3333',
    organization_id: 'org-enterprise-01',
    owner_id: 'user-001',
    name: 'Knowledge Engine Core Scaling',
    description: 'Upgrading hybrid RAG vector similarity search and multi-tenant persistence layer.',
    status: 'ACTIVE',
    priority: 'CRITICAL',
    document_count: 24,
    meeting_count: 5,
    task_count: 12,
    is_deleted: false,
    created_at: '2026-10-01T10:00:00Z',
  },
  {
    id: 'proj-4444-5555-6666',
    organization_id: 'org-enterprise-01',
    owner_id: 'user-002',
    name: 'Enterprise Security & Audit Compliance',
    description: 'Zero-trust RBAC permissions enforcement and automated audit event logging.',
    status: 'ACTIVE',
    priority: 'HIGH',
    document_count: 14,
    meeting_count: 3,
    task_count: 8,
    is_deleted: false,
    created_at: '2026-10-03T14:30:00Z',
  },
];

const MOCK_MEETINGS: Meeting[] = [
  {
    id: 'meet-1111-2222-3333',
    organization_id: 'org-enterprise-01',
    project_id: 'proj-1111-2222-3333',
    organizer_id: 'user-001',
    title: 'Phase 1.3 Database Architecture Review',
    scheduled_start: '2026-10-08T14:00:00Z',
    scheduled_end: '2026-10-08T15:00:00Z',
    recording_url: 'https://storage.enterprise.com/recordings/meet-1.mp4',
    transcript_text: 'Reviewed SQLAlchemy models, Alembic migrations, and index performance.',
    summary_text: 'Validated PostgreSQL 16 schema, tenant FK constraints, and pgvector HNSW indexing.',
    is_deleted: false,
    created_at: '2026-10-08T12:00:00Z',
  },
];

const MOCK_TASKS: Task[] = [
  {
    id: 'task-1111-2222-3333',
    organization_id: 'org-enterprise-01',
    project_id: 'proj-1111-2222-3333',
    creator_id: 'user-001',
    assignee_id: 'user-003',
    title: 'Validate PostgreSQL pgvector HNSW vector index performance',
    description: 'Ensure query latency remains under 50ms for 100,000 vector chunks.',
    priority: 'CRITICAL',
    status: 'IN_PROGRESS',
    due_date: '2026-10-15T18:00:00Z',
    is_deleted: false,
    created_at: '2026-10-05T09:00:00Z',
  },
  {
    id: 'task-4444-5555-6666',
    organization_id: 'org-enterprise-01',
    project_id: 'proj-4444-5555-6666',
    creator_id: 'user-002',
    assignee_id: 'user-002',
    title: 'Verify Alembic upgrade head schema migration',
    description: 'Test migration rollback and schema deployment on local dev database.',
    priority: 'HIGH',
    status: 'DONE',
    due_date: '2026-10-08T17:00:00Z',
    is_deleted: false,
    created_at: '2026-10-06T11:00:00Z',
  },
];

const MOCK_KG_ENTITIES: KgEntity[] = [
  {
    id: 'ent-1',
    organization_id: 'org-enterprise-01',
    name: 'PostgreSQL 16',
    entity_type: 'Technology',
    description: 'Primary relational database engine supporting multi-tenant JSONB and vector storage.',
    properties: { version: '16.2' },
    created_at: '2026-10-01T00:00:00Z',
  },
  {
    id: 'ent-2',
    organization_id: 'org-enterprise-01',
    name: 'Hybrid RAG Pipeline',
    entity_type: 'Project',
    description: 'Multi-stage search merging dense cosine similarity with sparse BM25 lexical ranking.',
    properties: {},
    created_at: '2026-10-02T00:00:00Z',
  },
];

const MOCK_KG_RELATIONSHIPS: KgRelationship[] = [
  {
    id: 'rel-1',
    organization_id: 'org-enterprise-01',
    source_entity_id: 'ent-2',
    target_entity_id: 'ent-1',
    relation_type: 'DEPENDS_ON',
    weight: 1.0,
    confidence_score: 0.98,
    properties: {},
    created_at: '2026-10-02T00:00:00Z',
  },
];

const MOCK_LOGS: ActivityLog[] = [
  {
    id: 'log-1',
    organization_id: 'org-enterprise-01',
    user_id: 'user-001',
    user_full_name: 'Jane Doe',
    action: 'USER_LOGIN',
    resource_type: 'auth',
    ip_address: '192.168.1.100',
    metadata_json: { method: 'bearer_jwt' },
    created_at: '2026-10-08T22:00:00Z',
  },
  {
    id: 'log-2',
    organization_id: 'org-enterprise-01',
    user_id: 'user-002',
    user_full_name: 'John Smith',
    action: 'DOCUMENT_UPLOAD',
    resource_type: 'document',
    resource_id: 'doc-999',
    ip_address: '192.168.1.105',
    metadata_json: { filename: 'Q3_Review.pdf', size: 2458120 },
    created_at: '2026-10-08T21:45:00Z',
  },
];

export const DashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'projects' | 'meetings' | 'tasks' | 'knowledge' | 'audit'>('overview');

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Enterprise Workspace Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Database-driven platform telemetry, persistence layer monitoring, and multi-tenant entities.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border overflow-x-auto">
          <Button
            size="sm"
            variant={activeTab === 'overview' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('overview')}
            className="text-xs"
          >
            Overview
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'projects' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('projects')}
            className="text-xs flex items-center gap-1.5"
          >
            <FolderGit2 className="w-3.5 h-3.5" /> Projects
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'meetings' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('meetings')}
            className="text-xs flex items-center gap-1.5"
          >
            <Video className="w-3.5 h-3.5" /> Meetings
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'tasks' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('tasks')}
            className="text-xs flex items-center gap-1.5"
          >
            <CheckSquare className="w-3.5 h-3.5" /> Tasks
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'knowledge' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('knowledge')}
            className="text-xs flex items-center gap-1.5"
          >
            <Network className="w-3.5 h-3.5" /> Graph
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'audit' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('audit')}
            className="text-xs flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5" /> Audit Logs
          </Button>
        </div>
      </div>

      {/* Top telemetry metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Ingested Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,248</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center text-emerald-600 dark:text-emerald-400">
              <ArrowUpRight className="h-3.5 w-3.5 mr-0.5" />
              +14% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Indexed Chunks</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">48,920</div>
            <p className="text-xs text-muted-foreground mt-1">
              pgvector 1536-dim embeddings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Knowledge Graph Nodes</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3,412</div>
            <p className="text-xs text-muted-foreground mt-1">
              8,109 semantic relationships
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Collaborators</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">84</div>
            <p className="text-xs text-muted-foreground mt-1">
              Across 5 departments
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tab content view */}
      {activeTab === 'overview' && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Ingestion Queue</CardTitle>
              <CardDescription>Status of recent documents submitted to Celery</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-2.5 rounded-lg border border-border">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-4 w-4 text-primary" />
                    <div>
                      <div className="text-sm font-medium">Q3_Financial_Review.pdf</div>
                      <div className="text-xs text-muted-foreground">4.2 MB &bull; Finance</div>
                    </div>
                  </div>
                  <Badge variant="processed">PROCESSED</Badge>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg border border-border">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-4 w-4 text-primary" />
                    <div>
                      <div className="text-sm font-medium">Architecture_Blueprint_v2.docx</div>
                      <div className="text-xs text-muted-foreground">1.8 MB &bull; Engineering</div>
                    </div>
                  </div>
                  <Badge variant="processing">PROCESSING</Badge>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg border border-border">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-4 w-4 text-primary" />
                    <div>
                      <div className="text-sm font-medium">Annual_Security_Audit.pdf</div>
                      <div className="text-xs text-muted-foreground">8.4 MB &bull; Compliance</div>
                    </div>
                  </div>
                  <Badge variant="pending">PENDING</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Hybrid Search Distribution</CardTitle>
              <CardDescription>Vector vs Full-text search utilization</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span>Dense Semantic Retrieval (pgvector)</span>
                  <span>68%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: '68%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span>Sparse Keyword BM25</span>
                  <span>24%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-sky-500 rounded-full" style={{ width: '24%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span>Knowledge Graph Traversal</span>
                  <span>8%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: '8%' }} />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'projects' && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Enterprise Project Workspaces</h2>
          <ProjectList projects={MOCK_PROJECTS} />
        </Card>
      )}

      {activeTab === 'meetings' && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Scheduled & Transcribed Meetings</h2>
          <MeetingList meetings={MOCK_MEETINGS} />
        </Card>
      )}

      {activeTab === 'tasks' && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Action Item Tasks</h2>
          <TaskList tasks={MOCK_TASKS} />
        </Card>
      )}

      {activeTab === 'knowledge' && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Knowledge Graph Entities & Relationships</h2>
          <KnowledgeGraphView entities={MOCK_KG_ENTITIES} relationships={MOCK_KG_RELATIONSHIPS} />
        </Card>
      )}

      {activeTab === 'audit' && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Security & Persistence Audit Trail</h2>
          <ActivityLogTable logs={MOCK_LOGS} />
        </Card>
      )}
    </div>
  );
};
