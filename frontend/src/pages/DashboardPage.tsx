import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { DashboardProvider } from '@/context/DashboardContext';
import {
  WelcomeSection,
  KPICardGrid,
  ProjectsWidget,
  DocumentsWidget,
  ActivityFeedWidget,
  AIAssistantWidget,
  NotificationsWidget,
  AnalyticsWidget,
} from '@/features/dashboard';
import { ProjectList } from '@/features/projects/ProjectList';
import { MeetingList } from '@/features/meetings/MeetingList';
import { TaskList } from '@/features/tasks/TaskList';
import { KnowledgeGraphView } from '@/features/knowledge/KnowledgeGraphView';
import { ActivityLogTable } from '@/features/activity/ActivityLogTable';
import { PermissionGate } from '@/components/authorization/PermissionGate';
import { useAuthorization } from '@/hooks/useAuthorization';
import type { Project } from '@/types/project';
import type { Meeting } from '@/types/meeting';
import type { Task } from '@/types/task';
import type { KgEntity, KgRelationship } from '@/types/knowledge';
import type { ActivityLog } from '@/types/activity';
import {
  FolderGit2,
  Video,
  CheckSquare,
  Network,
  Activity,
  LayoutDashboard,
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

export const DashboardPageContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'projects' | 'meetings' | 'tasks' | 'knowledge' | 'audit'>('overview');
  const { isRole, can } = useAuthorization();
  const canViewAnalytics = can('analytics.view') || isRole(['OrgAdmin', 'SuperAdmin']);

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-6 px-4 sm:px-6">
      {/* Top Header & Navigation Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            Enterprise Command Center
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Real-time organizational telemetry, AI assistants, documents, and workspace coordination.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border overflow-x-auto shrink-0">
          <Button
            size="sm"
            variant={activeTab === 'overview' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('overview')}
            className="text-xs flex items-center gap-1.5"
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Overview
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'projects' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('projects')}
            className="text-xs flex items-center gap-1.5"
          >
            <FolderGit2 className="w-3.5 h-3.5" />
            Projects
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'meetings' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('meetings')}
            className="text-xs flex items-center gap-1.5"
          >
            <Video className="w-3.5 h-3.5" />
            Meetings
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'tasks' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('tasks')}
            className="text-xs flex items-center gap-1.5"
          >
            <CheckSquare className="w-3.5 h-3.5" />
            Tasks
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'knowledge' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('knowledge')}
            className="text-xs flex items-center gap-1.5"
          >
            <Network className="w-3.5 h-3.5" />
            Graph
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'audit' ? 'secondary' : 'ghost'}
            onClick={() => setActiveTab('audit')}
            className="text-xs flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5" />
            Audit
          </Button>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Chapter 7: Personalized Welcome Section */}
          <WelcomeSection />

          {/* Chapter 8: KPI Cards */}
          <KPICardGrid />

          {/* Chapter 4 & 21: Enterprise Main Workspace Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left & Center Columns (Span 2) */}
            <div className="lg:col-span-2 space-y-6">
              {/* Active Projects Widget */}
              <ProjectsWidget />

              {/* Recent Documents Widget */}
              <DocumentsWidget />

              {/* Recent Activity Feed */}
              <ActivityFeedWidget />

              {/* Analytics Widget (OrgAdmin / SuperAdmin) */}
              <PermissionGate
                permission="analytics.view"
                fallback={
                  canViewAnalytics ? <AnalyticsWidget /> : null
                }
              >
                <AnalyticsWidget />
              </PermissionGate>
            </div>

            {/* Right Column / Assistant & Notification Lane (Span 1) */}
            <div className="space-y-6">
              {/* Chapter 12: Lightweight AI Assistant Widget */}
              <AIAssistantWidget />

              {/* Chapter 13: Notifications Center Widget */}
              <NotificationsWidget />
            </div>
          </div>
        </div>
      )}

      {/* Subsystem Deep Dive Tabs */}
      {activeTab === 'projects' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Enterprise Project Workspaces</h2>
          </div>
          <ProjectList projects={MOCK_PROJECTS} />
        </Card>
      )}

      {activeTab === 'meetings' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Scheduled & Transcribed Meetings</h2>
          </div>
          <MeetingList meetings={MOCK_MEETINGS} />
        </Card>
      )}

      {activeTab === 'tasks' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Action Item Tasks</h2>
          </div>
          <TaskList tasks={MOCK_TASKS} />
        </Card>
      )}

      {activeTab === 'knowledge' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Knowledge Graph Entities & Relationships</h2>
          </div>
          <KnowledgeGraphView entities={MOCK_KG_ENTITIES} relationships={MOCK_KG_RELATIONSHIPS} />
        </Card>
      )}

      {activeTab === 'audit' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Security & Persistence Audit Trail</h2>
          </div>
          <ActivityLogTable logs={MOCK_LOGS} />
        </Card>
      )}
    </div>
  );
};

export const DashboardPage: React.FC = () => {
  return (
    <DashboardProvider>
      <DashboardPageContent />
    </DashboardProvider>
  );
};

export default DashboardPage;
