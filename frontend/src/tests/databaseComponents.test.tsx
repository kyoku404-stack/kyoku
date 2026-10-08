import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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

describe('Phase 1.3 Database-Driven UI Components', () => {
  describe('ProjectList Component', () => {
    it('renders empty card when projects array is empty', () => {
      render(<ProjectList projects={[]} />);
      expect(screen.getByText('No projects found')).toBeInTheDocument();
    });

    it('renders list of projects with name, badges, and metadata', () => {
      const projects: Project[] = [
        {
          id: 'proj-1234-5678',
          organization_id: 'org1',
          owner_id: 'user1',
          name: 'AI Search Hub',
          description: 'Vector search workspace',
          status: 'ACTIVE',
          priority: 'CRITICAL',
          document_count: 12,
          is_deleted: false,
          created_at: '2026-10-01T00:00:00Z',
        },
      ];

      const onSelect = vi.fn();
      render(<ProjectList projects={projects} onSelectProject={onSelect} />);

      expect(screen.getByText('AI Search Hub')).toBeInTheDocument();
      expect(screen.getByText('Vector search workspace')).toBeInTheDocument();
      expect(screen.getByText('Critical')).toBeInTheDocument();
      expect(screen.getByText('12 docs')).toBeInTheDocument();

      fireEvent.click(screen.getByText('AI Search Hub'));
      expect(onSelect).toHaveBeenCalledWith(projects[0]);
    });
  });

  describe('MeetingList Component', () => {
    it('renders empty message when no meetings exist', () => {
      render(<MeetingList meetings={[]} />);
      expect(screen.getByText('No meetings logged')).toBeInTheDocument();
    });

    it('renders meeting details and AI summary badge', () => {
      const meetings: Meeting[] = [
        {
          id: 'm-123',
          organization_id: 'org1',
          organizer_id: 'u-admin',
          title: 'Sprint Demo & Architecture',
          scheduled_start: '2026-10-08T10:00:00Z',
          scheduled_end: '2026-10-08T11:00:00Z',
          summary_text: 'Reviewed persistence layer schema and vector indexing.',
          is_deleted: false,
          created_at: '2026-10-08T09:00:00Z',
        },
      ];

      render(<MeetingList meetings={meetings} />);

      expect(screen.getByText('Sprint Demo & Architecture')).toBeInTheDocument();
      expect(screen.getByText('AI Summarized')).toBeInTheDocument();
      expect(screen.getByText(/Reviewed persistence layer schema/i)).toBeInTheDocument();
    });
  });

  describe('TaskList Component', () => {
    it('renders empty card when tasks array is empty', () => {
      render(<TaskList tasks={[]} />);
      expect(screen.getByText('No tasks found')).toBeInTheDocument();
    });

    it('renders tasks and triggers status toggle handler', () => {
      const tasks: Task[] = [
        {
          id: 't-1',
          organization_id: 'org1',
          creator_id: 'u1',
          title: 'Verify Alembic migration script',
          priority: 'HIGH',
          status: 'TODO',
          is_deleted: false,
          created_at: '2026-10-01T00:00:00Z',
        },
      ];

      const onToggle = vi.fn();
      render(<TaskList tasks={tasks} onToggleStatus={onToggle} />);

      expect(screen.getByText('Verify Alembic migration script')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByText('To Do')).toBeInTheDocument();

      fireEvent.click(screen.getByTitle('Toggle task status'));
      expect(onToggle).toHaveBeenCalledWith(tasks[0]);
    });
  });

  describe('KnowledgeGraphView Component', () => {
    it('renders empty graph message when entities array is empty', () => {
      render(<KnowledgeGraphView entities={[]} relationships={[]} />);
      expect(screen.getByText('Knowledge Graph empty')).toBeInTheDocument();
    });

    it('renders entities and directed relationship edges', () => {
      const entities: KgEntity[] = [
        {
          id: 'e1',
          organization_id: 'org1',
          name: 'FastAPI Engine',
          entity_type: 'Technology',
          description: 'REST and SSE API framework',
          properties: {},
          created_at: '2026-10-01T00:00:00Z',
        },
        {
          id: 'e2',
          organization_id: 'org1',
          name: 'PostgreSQL 16',
          entity_type: 'Technology',
          description: 'Multi-tenant relational database',
          properties: {},
          created_at: '2026-10-01T00:00:00Z',
        },
      ];

      const relationships: KgRelationship[] = [
        {
          id: 'r1',
          organization_id: 'org1',
          source_entity_id: 'e1',
          target_entity_id: 'e2',
          relation_type: 'DEPENDS_ON',
          weight: 1.0,
          confidence_score: 0.99,
          properties: {},
          created_at: '2026-10-01T00:00:00Z',
        },
      ];

      render(<KnowledgeGraphView entities={entities} relationships={relationships} />);

      expect(screen.getAllByText('FastAPI Engine')[0]).toBeInTheDocument();
      expect(screen.getAllByText('PostgreSQL 16')[0]).toBeInTheDocument();
      expect(screen.getByText('DEPENDS_ON')).toBeInTheDocument();
      expect(screen.getByText('Weight: 1')).toBeInTheDocument();
    });
  });

  describe('ActivityLogTable Component', () => {
    it('renders empty message when no logs exist', () => {
      render(<ActivityLogTable logs={[]} />);
      expect(screen.getByText('No audit logs recorded')).toBeInTheDocument();
    });

    it('renders table rows for audit logs', () => {
      const logs: ActivityLog[] = [
        {
          id: 'log-1',
          organization_id: 'org1',
          user_id: 'user-001',
          user_full_name: 'Jane Doe',
          action: 'USER_LOGIN',
          resource_type: 'auth',
          ip_address: '10.0.0.1',
          metadata_json: {},
          created_at: '2026-10-08T12:00:00Z',
        },
      ];

      render(<ActivityLogTable logs={logs} />);

      expect(screen.getByText('USER_LOGIN')).toBeInTheDocument();
      expect(screen.getByText('auth')).toBeInTheDocument();
      expect(screen.getByText('Jane Doe')).toBeInTheDocument();
      expect(screen.getByText('10.0.0.1')).toBeInTheDocument();
    });
  });
});
