import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import {
  WelcomeSection,
  KPICardGrid,
  ProjectsWidget,
  DocumentsWidget,
  ActivityFeedWidget,
  NotificationsWidget,
  NotificationCenter,
  GlobalSearchBar,
  AnalyticsWidget,
  AIAssistantWidget,
} from '@/features/dashboard';
import { DashboardPage } from '@/pages/DashboardPage';
import { dashboardService } from '@/services/dashboardService';
import type { UserProfileResponse } from '@/types/auth';
import type { DashboardSummary } from '@/types/dashboard';

vi.mock('@/services/dashboardService', () => ({
  dashboardService: {
    getDashboardSummary: vi.fn(),
    getActivityFeed: vi.fn(),
    getRecentProjects: vi.fn(),
    getRecentDocuments: vi.fn(),
    getNotifications: vi.fn(),
    markNotificationRead: vi.fn(),
    markAllNotificationsRead: vi.fn(),
    getAnalyticsSummary: vi.fn(),
    globalSearch: vi.fn(),
    streamAIQuery: vi.fn().mockImplementation((_req, callbacks) => {
      callbacks?.onToken?.('Hello from KEEP');
      callbacks?.onDone?.({ sources: [] });
      return Promise.resolve();
    }),
  },
}));

const mockUser: UserProfileResponse = {
  id: 'user-001',
  email: 'siddhant@openai.corp',
  full_name: 'Siddhant Sharma',
  role: 'OrgAdmin',
  organization_id: 'org-enterprise-01',
  is_active: true,
  created_at: '2026-10-01T00:00:00Z',
};

const mockSummary: DashboardSummary = {
  user: {
    id: 'user-001',
    full_name: 'Siddhant Sharma',
    email: 'siddhant@openai.corp',
    role: 'OrgAdmin',
  },
  organization: {
    id: 'org-enterprise-01',
    name: 'OpenAI Technologies',
    plan: 'enterprise',
  },
  kpi: {
    total_projects: 5,
    total_documents: 1248,
    total_members: 84,
    upcoming_meetings: 2,
    storage_used_bytes: 5368709120, // 5 GB
    storage_quota_bytes: 21474836480, // 20 GB
    ai_queries_today: 42,
  },
  greeting_time_of_day: 'morning',
};

const wrapSuccess = <T,>(data: T) => ({
  success: true,
  message: 'OK',
  data,
});

describe('Phase 1.7 Dashboard UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clearAuth();
    useAuthStore.getState().setAuth(mockUser, 'mock-jwt-token');

    vi.mocked(dashboardService.getDashboardSummary).mockResolvedValue(wrapSuccess(mockSummary));
    vi.mocked(dashboardService.getRecentProjects).mockResolvedValue(
      wrapSuccess([
        {
          id: 'p-1',
          name: 'Knowledge Retrieval Platform',
          description: 'Vector embeddings and hybrid search',
          status: 'active',
          priority: 'critical',
          progress_percent: 78,
          deadline: '2026-10-30',
          team_members: [{ id: 'u-1', full_name: 'Alice Lee' }],
          document_count: 12,
          updated_at: '2026-10-15T09:00:00Z',
        },
      ])
    );
    vi.mocked(dashboardService.getRecentDocuments).mockResolvedValue(
      wrapSuccess([
        {
          id: 'd-1',
          title: 'System_Architecture_v2.pdf',
          file_type: 'pdf',
          file_size_bytes: 2097152,
          project_id: 'p-1',
          project_name: 'Knowledge Retrieval Platform',
          uploaded_by: { id: 'u-1', full_name: 'Alice Lee' },
          uploaded_at: '2026-10-15T08:30:00Z',
          last_accessed_at: '2026-10-15T09:00:00Z',
          ai_summary_available: true,
        },
      ])
    );
    vi.mocked(dashboardService.getActivityFeed).mockResolvedValue(
      wrapSuccess({
        items: [
          {
            id: 'ev-1',
            actor: { id: 'u-1', full_name: 'Alice Lee' },
            action: 'uploaded',
            resource_type: 'document',
            resource_name: 'System_Architecture_v2.pdf',
            occurred_at: '2026-10-15T08:30:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      })
    );
    vi.mocked(dashboardService.getNotifications).mockResolvedValue(
      wrapSuccess({
        items: [
          {
            id: 'notif-1',
            type: 'info',
            category: 'info',
            title: 'Document Processed',
            body: 'AI indexing is complete.',
            message: 'AI indexing is complete.',
            is_read: false,
            created_at: '2026-10-15T08:30:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 15,
        total_pages: 1,
      })
    );
    vi.mocked(dashboardService.getAnalyticsSummary).mockResolvedValue(
      wrapSuccess({
        period: 'week',
        documents_uploaded: [
          { label: 'Mon', value: 12 },
          { label: 'Tue', value: 18 },
        ],
        active_users: [
          { label: 'Mon', value: 45 },
          { label: 'Tue', value: 60 },
        ],
        new_members: [],
        project_distribution: [{ status: 'active', count: 5 }],
        ai_usage_trend: [],
        search_trend: [],
      })
    );
    vi.mocked(dashboardService.globalSearch).mockResolvedValue(
      wrapSuccess({
        query: 'System',
        total: 1,
        items: [
          {
            type: 'document',
            id: 'd-1',
            title: 'System_Architecture_v2.pdf',
            subtitle: 'Knowledge Retrieval Platform',
            url: '/documents/d-1',
            icon: 'file',
            relevance_score: 0.98,
          },
        ],
      })
    );
  });

  describe('WelcomeSection Widget', () => {
    it('renders greeting, user full name, organization, and quick metrics', () => {
      render(
        <MemoryRouter>
          <WelcomeSection summary={mockSummary} isLoading={false} />
        </MemoryRouter>
      );

      expect(screen.getByText(/Good morning/i)).toBeInTheDocument();
      expect(screen.getByText('Siddhant Sharma')).toBeInTheDocument();
      expect(screen.getByText(/OpenAI Technologies/i)).toBeInTheDocument();
      expect(screen.getByText('enterprise')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument(); // active projects
      expect(screen.getByText('1248')).toBeInTheDocument(); // documents
    });

    it('renders skeleton pulse state while loading', () => {
      const { container } = render(
        <MemoryRouter>
          <WelcomeSection summary={null} isLoading={true} />
        </MemoryRouter>
      );

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  describe('KPICardGrid Widget', () => {
    it('renders all key KPI telemetry cards and quota bar', () => {
      render(
        <MemoryRouter>
          <KPICardGrid kpi={mockSummary.kpi} isLoading={false} />
        </MemoryRouter>
      );

      expect(screen.getByText('Total Projects')).toBeInTheDocument();
      expect(screen.getByText('Documents')).toBeInTheDocument();
      expect(screen.getByText('1248')).toBeInTheDocument();
      expect(screen.getByText('Storage Usage')).toBeInTheDocument();
      expect(screen.getByText('AI Queries')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });
  });

  describe('ProjectsWidget', () => {
    it('fetches and renders project list with progress indicator', async () => {
      render(
        <MemoryRouter>
          <ProjectsWidget />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Knowledge Retrieval Platform')).toBeInTheDocument();
      });
      expect(screen.getByText('78%')).toBeInTheDocument();
      expect(screen.getByText('Critical')).toBeInTheDocument();
    });
  });

  describe('DocumentsWidget', () => {
    it('renders recent documents with AI summary badge', async () => {
      render(
        <MemoryRouter>
          <DocumentsWidget />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('System_Architecture_v2.pdf')).toBeInTheDocument();
      });
      expect(screen.getByText(/AI Ready/i)).toBeInTheDocument();
    });
  });

  describe('ActivityFeedWidget', () => {
    it('renders chronological activity events and handles filter category change', async () => {
      render(
        <MemoryRouter>
          <ActivityFeedWidget />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('System_Architecture_v2.pdf')).toBeInTheDocument();
      });
      expect(screen.getByText('Alice Lee')).toBeInTheDocument();

      const filterSelect = screen.getByLabelText(/Filter activity by resource type/i);
      fireEvent.change(filterSelect, { target: { value: 'document' } });

      await waitFor(() => {
        expect(dashboardService.getActivityFeed).toHaveBeenCalledWith(
          expect.objectContaining({ filter: 'document' })
        );
      });
    });
  });

  describe('NotificationCenter Component', () => {
    it('renders notification bell with unread badge and opens popover', async () => {
      render(
        <MemoryRouter>
          <NotificationCenter />
        </MemoryRouter>
      );

      const bellBtn = screen.getByRole('button', { name: /notifications/i });
      expect(bellBtn).toBeInTheDocument();

      fireEvent.click(bellBtn);

      await waitFor(() => {
        expect(screen.getByText('Document Processed')).toBeInTheDocument();
      });
      expect(screen.getByText('AI indexing is complete.')).toBeInTheDocument();
    });
  });

  describe('NotificationsWidget Component', () => {
    it('displays notifications list and allows marking as read', async () => {
      vi.mocked(dashboardService.markNotificationRead).mockResolvedValueOnce(
        wrapSuccess({
          id: 'notif-1',
          type: 'info',
          title: 'Document Processed',
          body: 'AI indexing is complete.',
          is_read: true,
          created_at: '2026-10-15T08:30:00Z',
        })
      );

      render(
        <MemoryRouter>
          <NotificationsWidget />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Document Processed')).toBeInTheDocument();
      });

      const markBtn = screen.getByTitle(/mark as read/i);
      fireEvent.click(markBtn);

      await waitFor(() => {
        expect(dashboardService.markNotificationRead).toHaveBeenCalledWith('notif-1');
      });
    });
  });

  describe('AnalyticsWidget Component', () => {
    it('renders time series summaries and switches periods', async () => {
      render(
        <MemoryRouter>
          <AnalyticsWidget />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Organizational Analytics/i)).toBeInTheDocument();
      });

      const monthBtn = screen.getByRole('button', { name: /^month$/i });
      fireEvent.click(monthBtn);

      await waitFor(() => {
        expect(dashboardService.getAnalyticsSummary).toHaveBeenCalledWith('month');
      });
    });
  });

  describe('GlobalSearchBar Component', () => {
    it('allows typing queries and displaying matching search items', async () => {
      render(
        <MemoryRouter>
          <GlobalSearchBar />
        </MemoryRouter>
      );

      const input = screen.getByLabelText(/global search query/i);
      fireEvent.change(input, { target: { value: 'System' } });

      await waitFor(
        () => {
          expect(dashboardService.globalSearch).toHaveBeenCalledWith(
            expect.objectContaining({ q: 'System' })
          );
        },
        { timeout: 1000 }
      );
    });
  });

  describe('AIAssistantWidget Component', () => {
    it('renders role-tailored prompt suggestion chips and triggers query on click', () => {
      render(
        <MemoryRouter>
          <AIAssistantWidget />
        </MemoryRouter>
      );

      expect(screen.getByText(/AI Knowledge Assistant/i)).toBeInTheDocument();
      const chip = screen.getByText(/"Summarize this week's activity across projects"/i);
      expect(chip).toBeInTheDocument();

      fireEvent.click(chip);
      expect(dashboardService.streamAIQuery).toHaveBeenCalled();
    });
  });

  describe('Master DashboardPage Integration', () => {
    it('assembles the full enterprise workspace under DashboardProvider', async () => {
      render(
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/Enterprise Command Center/i)).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByText('Siddhant Sharma')).toBeInTheDocument();
      });
    });
  });
});
