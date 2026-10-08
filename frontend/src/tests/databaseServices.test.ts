import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '@/services/api';
import {
  projectService,
  teamService,
  meetingService,
  taskService,
  knowledgeService,
  activityService,
} from '@/services';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type { Project } from '@/types/project';
import type { Team } from '@/types/team';
import type { Meeting } from '@/types/meeting';
import type { Task } from '@/types/task';
import type { KgQueryResponse } from '@/types/knowledge';
import type { ActivityLog } from '@/types/activity';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      defaults: { baseURL: 'http://localhost:8000/api/v1' },
    },
  };
});

describe('Phase 1.3 Persistence Domain Services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('projectService', () => {
    it('listProjects calls /projects with filter params', async () => {
      const mockResponse: ApiResponse<PaginatedData<Project>> = {
        success: true,
        message: 'Projects retrieved.',
        data: {
          items: [
            {
              id: 'p1',
              organization_id: 'org1',
              owner_id: 'u1',
              name: 'Core RAG Engine',
              status: 'ACTIVE',
              priority: 'HIGH',
              is_deleted: false,
              created_at: '2026-10-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const res = await projectService.listProjects({ status: 'ACTIVE' });
      expect(apiClient.get).toHaveBeenCalledWith('/projects', {
        params: { status: 'ACTIVE' },
      });
      expect(res.data.items[0].name).toBe('Core RAG Engine');
    });

    it('createProject calls POST /projects', async () => {
      const mockResponse: ApiResponse<Project> = {
        success: true,
        message: 'Project created.',
        data: {
          id: 'p2',
          organization_id: 'org1',
          owner_id: 'u1',
          name: 'New Workspace',
          status: 'ACTIVE',
          priority: 'MEDIUM',
          is_deleted: false,
          created_at: '2026-10-01T00:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const res = await projectService.createProject({
        name: 'New Workspace',
        priority: 'MEDIUM',
      });
      expect(apiClient.post).toHaveBeenCalledWith('/projects', {
        name: 'New Workspace',
        priority: 'MEDIUM',
      });
      expect(res.data.id).toBe('p2');
    });
  });

  describe('teamService', () => {
    it('listTeams calls /teams', async () => {
      const mockResponse: ApiResponse<PaginatedData<Team>> = {
        success: true,
        message: 'Teams retrieved.',
        data: {
          items: [
            {
              id: 't1',
              organization_id: 'org1',
              name: 'Engineering',
              is_deleted: false,
              created_at: '2026-10-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const res = await teamService.listTeams();
      expect(apiClient.get).toHaveBeenCalledWith('/teams');
      expect(res.data.items[0].name).toBe('Engineering');
    });
  });

  describe('meetingService', () => {
    it('listMeetings calls /meetings with params', async () => {
      const mockResponse: ApiResponse<PaginatedData<Meeting>> = {
        success: true,
        message: 'Meetings retrieved.',
        data: {
          items: [
            {
              id: 'm1',
              organization_id: 'org1',
              organizer_id: 'u1',
              title: 'Sprint Sync',
              scheduled_start: '2026-10-08T10:00:00Z',
              scheduled_end: '2026-10-08T11:00:00Z',
              is_deleted: false,
              created_at: '2026-10-08T09:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const res = await meetingService.listMeetings({ page: 1 });
      expect(apiClient.get).toHaveBeenCalledWith('/meetings', {
        params: { page: 1 },
      });
      expect(res.data.items[0].title).toBe('Sprint Sync');
    });
  });

  describe('taskService', () => {
    it('listTasks calls /tasks with status filter', async () => {
      const mockResponse: ApiResponse<PaginatedData<Task>> = {
        success: true,
        message: 'Tasks retrieved.',
        data: {
          items: [
            {
              id: 'tk1',
              organization_id: 'org1',
              creator_id: 'u1',
              title: 'Fix pgvector indexing',
              priority: 'CRITICAL',
              status: 'IN_PROGRESS',
              is_deleted: false,
              created_at: '2026-10-08T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const res = await taskService.listTasks({ status: 'IN_PROGRESS' });
      expect(apiClient.get).toHaveBeenCalledWith('/tasks', {
        params: { status: 'IN_PROGRESS' },
      });
      expect(res.data.items[0].priority).toBe('CRITICAL');
    });
  });

  describe('knowledgeService', () => {
    it('queryGraph calls POST /graph/query', async () => {
      const mockResponse: ApiResponse<KgQueryResponse> = {
        success: true,
        message: 'Graph query executed.',
        data: {
          entities: [
            {
              id: 'e1',
              organization_id: 'org1',
              name: 'PostgreSQL',
              entity_type: 'Technology',
              properties: {},
              created_at: '2026-10-01T00:00:00Z',
            },
          ],
          relationships: [
            {
              id: 'r1',
              organization_id: 'org1',
              source_entity_id: 'e2',
              target_entity_id: 'e1',
              relation_type: 'DEPENDS_ON',
              weight: 1.0,
              confidence_score: 0.95,
              properties: {},
              created_at: '2026-10-01T00:00:00Z',
            },
          ],
          total_entities: 1,
          total_relationships: 1,
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const res = await knowledgeService.queryGraph({ entity_name: 'PostgreSQL' });
      expect(apiClient.post).toHaveBeenCalledWith('/graph/query', {
        entity_name: 'PostgreSQL',
      });
      expect(res.data.entities[0].name).toBe('PostgreSQL');
    });
  });

  describe('activityService', () => {
    it('listActivityLogs calls GET /activity-logs', async () => {
      const mockResponse: ApiResponse<PaginatedData<ActivityLog>> = {
        success: true,
        message: 'Logs retrieved.',
        data: {
          items: [
            {
              id: 'l1',
              organization_id: 'org1',
              user_id: 'u1',
              action: 'USER_LOGIN',
              resource_type: 'auth',
              metadata_json: {},
              created_at: '2026-10-08T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const res = await activityService.listActivityLogs({ page: 1 });
      expect(apiClient.get).toHaveBeenCalledWith('/activity-logs', {
        params: { page: 1 },
      });
      expect(res.data.items[0].action).toBe('USER_LOGIN');
    });
  });
});
