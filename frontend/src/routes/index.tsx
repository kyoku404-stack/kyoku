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
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage }))
);

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
          <SuspenseWrapper>
            <OrgSetupPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'organization/settings',
        element: (
          <SuspenseWrapper>
            <OrgSettingsPage />
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
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'upload',
        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
      {
        path: 'chat',
        element: (
          <SuspenseWrapper>
            <DashboardPage />
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
