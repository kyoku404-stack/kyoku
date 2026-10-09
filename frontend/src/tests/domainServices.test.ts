import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '@/services/api';
import {
  authService,
  userService,
  orgService,
  documentService,
  searchService,
  chatService,
  analyticsService,
  healthService,
} from '@/services';
import type { ApiResponse, PaginatedData } from '@/types/api';
import type {
  RefreshTokenResponse,
  TokenResponse,
  UserProfileResponse,
} from '@/types/auth';
import type { OrganizationResponse } from '@/types/organization';
import type {
  DocumentResponse,
  DocumentUploadResponse,
} from '@/types/document';
import type { SearchResponse } from '@/types/search';
import type { ChatQueryResponse } from '@/types/chat';
import type {
  AnalyticsSummaryResponse,
  UsageMetricsResponse,
} from '@/types/analytics';
import type { DetailedHealthResponse } from '@/types/health';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      defaults: { baseURL: 'http://localhost:8000/api/v1' },
    },
  };
});

describe('Domain API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('authService', () => {
    it('calls /auth/login with credentials and returns envelope', async () => {
      const mockResponse: ApiResponse<TokenResponse> = {
        success: true,
        message: 'Login successful.',
        data: {
          access_token: 'test_token',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: 'u1',
            email: 'user@enterprise.com',
            full_name: 'John Doe',
            role: 'OrgAdmin',
            organization_id: 'org1',
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await authService.login({
        email: 'user@enterprise.com',
        password: 'Password123!',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        email: 'user@enterprise.com',
        password: 'Password123!',
      });
      expect(result).toEqual(mockResponse);
      expect(result.data.access_token).toBe('test_token');
    });

    it('calls /auth/refresh with refresh token', async () => {
      const mockResponse: ApiResponse<RefreshTokenResponse> = {
        success: true,
        message: 'Token refreshed.',
        data: {
          access_token: 'new_token',
          token_type: 'bearer',
          expires_in: 3600,
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await authService.refreshToken('old_refresh_token');
      expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: 'old_refresh_token',
      });
      expect(result.data.access_token).toBe('new_token');
    });

    it('calls /auth/me to retrieve current user', async () => {
      const mockResponse: ApiResponse<UserProfileResponse> = {
        success: true,
        message: 'User retrieved.',
        data: {
          id: 'u1',
          email: 'user@enterprise.com',
          full_name: 'John Doe',
          role: 'Member',
          organization_id: 'org1',
          is_active: true,
          created_at: '2026-10-01T00:00:00Z',
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const result = await authService.getCurrentUser();
      expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
      expect(result.data.id).toBe('u1');
    });

    it('calls /auth/logout', async () => {
      const mockResponse: ApiResponse<{ user_id: string }> = {
        success: true,
        message: 'Logout successful.',
        data: { user_id: 'u1' },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await authService.logout();
      expect(apiClient.post).toHaveBeenCalledWith('/auth/logout', {});
      expect(result.data.user_id).toBe('u1');
    });
  });

  describe('userService', () => {
    it('calls /users with pagination parameters', async () => {
      const mockResponse: ApiResponse<PaginatedData<UserProfileResponse>> = {
        success: true,
        message: 'Users retrieved.',
        data: {
          items: [
            {
              id: 'u1',
              email: 'john@enterprise.com',
              full_name: 'John Doe',
              role: 'Member',
              organization_id: 'org1',
              is_active: true,
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

      const result = await userService.listUsers({ page: 1, page_size: 20 });
      expect(apiClient.get).toHaveBeenCalledWith('/users', {
        params: { page: 1, page_size: 20 },
      });
      expect(result.data.items).toHaveLength(1);
    });

    it('calls /users/{id} for user details', async () => {
      const mockResponse: ApiResponse<UserProfileResponse> = {
        success: true,
        message: 'User details retrieved.',
        data: {
          id: 'u-123',
          email: 'jane@enterprise.com',
          full_name: 'Jane Smith',
          role: 'Manager',
          organization_id: 'org1',
          is_active: true,
          created_at: '2026-10-01T00:00:00Z',
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const result = await userService.getUserById('u-123');
      expect(apiClient.get).toHaveBeenCalledWith('/users/u-123');
      expect(result.data.id).toBe('u-123');
    });
  });

  describe('orgService', () => {
    it('calls /organizations/current to get tenant info', async () => {
      const mockResponse: ApiResponse<OrganizationResponse> = {
        success: true,
        message: 'Organization details retrieved.',
        data: {
          id: 'org-1',
          name: 'Acme Enterprise',
          domain: 'acme.com',
          is_active: true,
          created_at: '2026-10-01T00:00:00Z',
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

      const result = await orgService.getCurrentOrganization();
      expect(apiClient.get).toHaveBeenCalledWith('/organizations/current');
      expect(result.data.domain).toBe('acme.com');
    });
  });

  describe('documentService', () => {
    it('uploads file with multipart header', async () => {
      const mockFile = new File(['sample content'], 'handbook.pdf', {
        type: 'application/pdf',
      });
      const mockResponse: ApiResponse<DocumentUploadResponse> = {
        success: true,
        message: 'Document accepted.',
        data: {
          document_id: 'doc-1',
          filename: 'handbook.pdf',
          status: 'PROCESSING',
          file_size: 14,
          created_at: '2026-10-01T00:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await documentService.uploadDocument(
        mockFile,
        'Employee Handbook',
        'policy,hr'
      );

      expect(apiClient.post).toHaveBeenCalledWith(
        '/documents/upload',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      expect(result.data.filename).toBe('handbook.pdf');
    });

    it('lists documents with query params', async () => {
      const mockResponse: ApiResponse<PaginatedData<DocumentResponse>> = {
        success: true,
        message: 'Documents retrieved.',
        data: {
          items: [
            {
              id: 'd1',
              filename: 'report.pdf',
              file_type: 'application/pdf',
              file_size: 1024,
              status: 'PROCESSED',
              chunk_count: 5,
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

      const result = await documentService.listDocuments({ page: 1 });
      expect(apiClient.get).toHaveBeenCalledWith('/documents', {
        params: { page: 1 },
      });
      expect(result.data.items).toHaveLength(1);
    });
  });

  describe('searchService', () => {
    it('executes hybrid search query', async () => {
      const mockResponse: ApiResponse<SearchResponse> = {
        success: true,
        message: 'Search executed.',
        data: {
          query: 'vacation policy',
          total_results: 1,
          results: [
            {
              chunk_id: 'c1',
              document_id: 'd1',
              filename: 'hr.pdf',
              content: 'Vacation accrues at 2 days per month.',
              relevance_score: 0.95,
            },
          ],
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await searchService.hybridSearch({
        query: 'vacation policy',
        top_k: 5,
      });

      expect(apiClient.post).toHaveBeenCalledWith('/search/hybrid', {
        query: 'vacation policy',
        top_k: 5,
      });
      expect(result.data.results[0].relevance_score).toBe(0.95);
    });
  });

  describe('chatService queryChat', () => {
    it('executes synchronous RAG question answering', async () => {
      const mockResponse: ApiResponse<ChatQueryResponse> = {
        success: true,
        message: 'Answer generated.',
        data: {
          query: 'What is the stipend?',
          answer: 'The annual stipend is $1,000.',
          conversation_id: 'conv-1',
          confidence_score: 0.98,
          model_name: 'gpt-4o',
          tokens_used: 120,
          citations: [
            {
              document_id: 'd1',
              filename: 'stipend.pdf',
              page_number: 2,
              snippet: '$1,000 per fiscal year',
              relevance_score: 0.98,
            },
          ],
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await chatService.queryChat({
        query: 'What is the stipend?',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/chat/query', {
        query: 'What is the stipend?',
      });
      expect(result.data.citations).toHaveLength(1);
    });
  });

  describe('analyticsService', () => {
    it('fetches summary and usage analytics', async () => {
      const summaryResp: ApiResponse<AnalyticsSummaryResponse> = {
        success: true,
        message: 'Summary',
        data: {
          total_documents: 42,
          total_queries: 1280,
          total_users: 15,
          active_sessions: 4,
          storage_used_bytes: 104857600,
        },
      };
      const usageResp: ApiResponse<UsageMetricsResponse> = {
        success: true,
        message: 'Usage',
        data: {
          queries_today: 342,
          tokens_consumed_today: 158200,
          avg_latency_ms: 245.5,
        },
      };

      vi.mocked(apiClient.get)
        .mockResolvedValueOnce({ data: summaryResp })
        .mockResolvedValueOnce({ data: usageResp });

      const summary = await analyticsService.getSummary();
      const usage = await analyticsService.getUsage();

      expect(apiClient.get).toHaveBeenCalledWith('/analytics/summary');
      expect(apiClient.get).toHaveBeenCalledWith('/analytics/usage');
      expect(summary.data.total_documents).toBe(42);
      expect(usage.data.queries_today).toBe(342);
    });
  });

  describe('healthService', () => {
    it('fetches basic and detailed health checks', async () => {
      const basicResp = {
        status: 'healthy',
        environment: 'testing',
        version: '1.2.0',
        timestamp: '2026-10-01T00:00:00Z',
      };
      const detailedResp: ApiResponse<DetailedHealthResponse> = {
        success: true,
        message: 'Details',
        data: {
          status: 'healthy',
          environment: 'testing',
          version: '1.2.0',
          timestamp: '2026-10-01T00:00:00Z',
          uptime_seconds: 120.5,
          components: {
            database: { status: 'healthy', latency_ms: 1.2 },
            redis: { status: 'healthy', latency_ms: 0.5 },
          },
        },
      };

      vi.mocked(apiClient.get)
        .mockResolvedValueOnce({ data: basicResp })
        .mockResolvedValueOnce({ data: detailedResp });

      const basic = await healthService.checkHealth();
      const detailed = await healthService.getDetailedHealth();

      expect(apiClient.get).toHaveBeenCalledWith('/health');
      expect(apiClient.get).toHaveBeenCalledWith('/health/details');
      expect(basic.status).toBe('healthy');
      expect(detailed.data.components.database.status).toBe('healthy');
    });
  });
});
