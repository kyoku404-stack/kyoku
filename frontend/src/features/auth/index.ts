/**
 * Auth Feature Module
 * User authentication, JWT sessions, password management, and RBAC profile management.
 */

export * from './LoginForm';
export * from './RegisterForm';
export * from './ForgotPasswordForm';
export * from './ResetPasswordForm';
export * from './ChangePasswordForm';
export * from './UserProfileView';

export const AUTH_FEATURE = {
  name: 'auth',
  version: '1.4.0',
  description: 'Enterprise authentication, JWT session lifecycle, and RBAC authorization',
};
