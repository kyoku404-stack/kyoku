import { Suspense, lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RootLayout } from '@/layouts/RootLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';

// Lazy-loaded page components for optimal code-splitting
const HomePage = lazy(() =>
  import('@/pages/HomePage').then((m) => ({ default: m.HomePage }))
);
const HealthPage = lazy(() =>
  import('@/pages/HealthPage').then((m) => ({ default: m.HealthPage }))
);
const ObservabilityPage = lazy(() =>
  import('@/pages/ObservabilityPage').then((m) => ({ default: m.ObservabilityPage }))
);
const IngestionPage = lazy(() =>
  import('@/pages/IngestionPage').then((m) => ({ default: m.IngestionPage }))
);
const RAGChatPage = lazy(() =>
  import('@/pages/RAGChatPage').then((m) => ({ default: m.RAGChatPage }))
);
const AssistantPage = lazy(() =>
  import('@/pages/AssistantPage').then((m) => ({ default: m.AssistantPage }))
);
const KnowledgeGraphPage = lazy(() =>
  import('@/pages/KnowledgeGraphPage').then((m) => ({ default: m.KnowledgeGraphPage }))
);
const EnterpriseIntelligencePage = lazy(() =>
  import('@/pages/EnterpriseIntelligencePage').then((m) => ({ default: m.EnterpriseIntelligencePage }))
);
const IntegrationsPage = lazy(() =>
  import('@/pages/IntegrationsPage').then((m) => ({ default: m.IntegrationsPage }))
);
const CollaborationPage = lazy(() =>
  import('@/pages/CollaborationPage').then((m) => ({ default: m.CollaborationPage }))
);
const SecurityGovernancePage = lazy(() =>
  import('@/pages/SecurityGovernancePage').then((m) => ({ default: m.SecurityGovernancePage }))
);
const WorkflowAutomationPage = lazy(() =>
  import('@/pages/WorkflowAutomationPage').then((m) => ({ default: m.WorkflowAutomationPage }))
);
const PluginManagementPage = lazy(() =>
  import('@/pages/PluginManagementPage').then((m) => ({ default: m.PluginManagementPage }))
);
const DashboardPage = lazy(() =>

  import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))
);
const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage }))
);
const RegisterPage = lazy(() =>
  import('@/pages/RegisterPage').then((m) => ({ default: m.RegisterPage }))
);
const ForgotPasswordPage = lazy(() =>
  import('@/pages/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage }))
);
const ResetPasswordPage = lazy(() =>
  import('@/pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage }))
);
const ProfilePage = lazy(() =>
  import('@/pages/ProfilePage').then((m) => ({ default: m.ProfilePage }))
);
const OrganizationPage = lazy(() =>
  import('@/pages/OrganizationPage').then((m) => ({ default: m.OrganizationPage }))
);
const OrgSetupPage = lazy(() =>
  import('@/pages/OrgSetupPage').then((m) => ({ default: m.OrgSetupPage }))
);
const DepartmentsPage = lazy(() =>
  import('@/pages/DepartmentsPage').then((m) => ({ default: m.DepartmentsPage }))
);
const TeamsPage = lazy(() =>
  import('@/pages/TeamsPage').then((m) => ({ default: m.TeamsPage }))
);
const ProjectsPage = lazy(() =>
  import('@/pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage }))
);
const MembersPage = lazy(() =>
  import('@/pages/MembersPage').then((m) => ({ default: m.MembersPage }))
);
const OrgSettingsPage = lazy(() =>
  import('@/pages/OrgSettingsPage').then((m) => ({ default: m.OrgSettingsPage }))
);
const AcceptInvitationPage = lazy(() =>
  import('@/pages/AcceptInvitationPage').then((m) => ({ default: m.AcceptInvitationPage }))
);
const AccessDeniedPage = lazy(() =>
  import('@/pages/AccessDeniedPage').then((m) => ({ default: m.AccessDeniedPage }))
);
const AuditLogsPage = lazy(() =>
  import('@/pages/AuditLogsPage').then((m) => ({ default: m.AuditLogsPage }))
);
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage }))
);
const DocumentsPage = lazy(() =>
  import('@/pages/DocumentsPage').then((m) => ({ default: m.DocumentsPage }))
);

import { RequirePermission, RequireRole } from '@/routes/guards';
import { Permission } from '@/types/permission';

const SuspenseWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense
    fallback={
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" label="Loading application module..." />
      </div>
    }
  >
    {children}
  </Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <HomePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'health',
        element: (
          <SuspenseWrapper>
            <HealthPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'observability',
        element: (
          <SuspenseWrapper>
            <ObservabilityPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'ingestion',
        element: (
          <SuspenseWrapper>
            <IngestionPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'dashboard',

        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'profile',
        element: (
          <SuspenseWrapper>
            <ProfilePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'organization',
        element: (
          <SuspenseWrapper>
            <OrganizationPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'organization/setup',
        element: (
          <RequireRole allowedRoles={['OrgAdmin', 'SuperAdmin']}>
            <SuspenseWrapper>
              <OrgSetupPage />
            </SuspenseWrapper>
          </RequireRole>
        ),
      },
      {
        path: 'organization/settings',
        element: (
          <RequirePermission permission={Permission.ORGANIZATION_SETTINGS}>
            <SuspenseWrapper>
              <OrgSettingsPage />
            </SuspenseWrapper>
          </RequirePermission>
        ),
      },
      {
        path: 'audit/logs',
        element: (
          <RequirePermission permission={Permission.AUDIT_READ}>
            <SuspenseWrapper>
              <AuditLogsPage />
            </SuspenseWrapper>
          </RequirePermission>
        ),
      },
      {
        path: 'access-denied',
        element: (
          <SuspenseWrapper>
            <AccessDeniedPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'departments',
        element: (
          <SuspenseWrapper>
            <DepartmentsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'teams',
        element: (
          <SuspenseWrapper>
            <TeamsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'projects',
        element: (
          <SuspenseWrapper>
            <ProjectsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'members',
        element: (
          <SuspenseWrapper>
            <MembersPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'search',
        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'documents',
        element: (
          <SuspenseWrapper>
            <DocumentsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'upload',
        element: (
          <SuspenseWrapper>
            <DocumentsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'chat',
        element: (
          <SuspenseWrapper>
            <RAGChatPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'rag',
        element: (
          <SuspenseWrapper>
            <RAGChatPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'assistant',
        element: (
          <SuspenseWrapper>
            <AssistantPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'ai-assistant',
        element: (
          <SuspenseWrapper>
            <AssistantPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'graph',
        element: (
          <SuspenseWrapper>
            <KnowledgeGraphPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'knowledge-graph',
        element: (
          <SuspenseWrapper>
            <KnowledgeGraphPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'intelligence',
        element: (
          <SuspenseWrapper>
            <EnterpriseIntelligencePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'enterprise-intelligence',
        element: (
          <SuspenseWrapper>
            <EnterpriseIntelligencePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'integrations',
        element: (
          <SuspenseWrapper>
            <IntegrationsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'connectors',
        element: (
          <SuspenseWrapper>
            <IntegrationsPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'collaboration',
        element: (
          <SuspenseWrapper>
            <CollaborationPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'workspaces',
        element: (
          <SuspenseWrapper>
            <CollaborationPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'security',
        element: (
          <SuspenseWrapper>
            <SecurityGovernancePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'compliance',
        element: (
          <SuspenseWrapper>
            <SecurityGovernancePage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'workflows',
        element: (
          <SuspenseWrapper>
            <WorkflowAutomationPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'notifications',
        element: (
          <SuspenseWrapper>
            <WorkflowAutomationPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'plugins',
        element: (
          <SuspenseWrapper>
            <PluginManagementPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'marketplace',
        element: (
          <SuspenseWrapper>
            <PluginManagementPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'meetings',
        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'analytics',
        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: '*',
        element: (
          <SuspenseWrapper>
            <NotFoundPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/invitations',
    element: <AuthLayout />,
    children: [
      {
        path: 'accept',
        element: (
          <SuspenseWrapper>
            <AcceptInvitationPage />
          </SuspenseWrapper>
        ),
      },
      {
        index: true,
        element: <Navigate to="/auth/login" replace />,
      },
    ],
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    children: [
      {
        path: 'login',
        element: (
          <SuspenseWrapper>
            <LoginPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'register',
        element: (
          <SuspenseWrapper>
            <RegisterPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'forgot-password',
        element: (
          <SuspenseWrapper>
            <ForgotPasswordPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'reset-password',
        element: (
          <SuspenseWrapper>
            <ResetPasswordPage />
          </SuspenseWrapper>
        ),
      },
      {
        index: true,
        element: <Navigate to="/auth/login" replace />,
      },
    ],
  },
  {
    path: '/login',
    element: <Navigate to="/auth/login" replace />,
  },
  {
    path: '/register',
    element: <Navigate to="/auth/register" replace />,
  },
]);
