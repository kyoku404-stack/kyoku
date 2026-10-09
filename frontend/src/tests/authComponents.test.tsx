import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginForm } from '@/features/auth/LoginForm';
import { RegisterForm } from '@/features/auth/RegisterForm';
import { ForgotPasswordForm } from '@/features/auth/ForgotPasswordForm';
import { ResetPasswordForm } from '@/features/auth/ResetPasswordForm';
import { UserProfileView } from '@/features/auth/UserProfileView';
import { ChangePasswordForm } from '@/features/auth/ChangePasswordForm';
import type { UserProfileResponse } from '@/types/auth';

describe('Phase 1.4 Auth & Identity UI Components', () => {
  describe('LoginForm Component', () => {
    it('renders input fields and submit button', () => {
      render(
        <MemoryRouter>
          <LoginForm />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText('user@enterprise.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('••••••••••••')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('shows validation error if submitted empty', () => {
      render(
        <MemoryRouter>
          <LoginForm />
        </MemoryRouter>
      );

      fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
      expect(screen.getByText('Please enter both email and password.')).toBeInTheDocument();
    });
  });

  describe('RegisterForm Component', () => {
    it('renders registration form with inputs and role selector', () => {
      render(
        <MemoryRouter>
          <RegisterForm />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText('Jane Doe')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('jane.doe@enterprise.com')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register account/i })).toBeInTheDocument();
    });
  });

  describe('ForgotPasswordForm Component', () => {
    it('renders email input for password reset link request', () => {
      render(
        <MemoryRouter>
          <ForgotPasswordForm />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText('user@enterprise.com')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    });
  });

  describe('ResetPasswordForm Component', () => {
    it('renders token and new password input fields', () => {
      render(
        <MemoryRouter>
          <ResetPasswordForm />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText('Paste your reset token')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm reset password/i })).toBeInTheDocument();
    });
  });

  describe('UserProfileView Component', () => {
    it('renders profile card with user details and RBAC role badge', () => {
      const mockUser: UserProfileResponse = {
        id: 'u-100',
        email: 'admin@enterprise.com',
        full_name: 'Super Admin',
        role: 'OrgAdmin',
        organization_id: 'org-1',
        is_active: true,
        is_verified: true,
        created_at: '2026-10-09T00:00:00Z',
      };

      render(<UserProfileView user={mockUser} />);

      expect(screen.getByText('Super Admin')).toBeInTheDocument();
      expect(screen.getByText('admin@enterprise.com')).toBeInTheDocument();
      expect(screen.getAllByText('OrgAdmin')[0]).toBeInTheDocument();
      expect(screen.getByText('Verified')).toBeInTheDocument();
    });
  });

  describe('ChangePasswordForm Component', () => {
    it('renders inputs for updating current password', () => {
      render(<ChangePasswordForm />);

      expect(screen.getByText('Change Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /update password/i })).toBeInTheDocument();
    });
  });
});
