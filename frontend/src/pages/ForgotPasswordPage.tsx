import React from 'react';
import { ForgotPasswordForm } from '@/features/auth/ForgotPasswordForm';

export const ForgotPasswordPage: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)] py-6">
      <ForgotPasswordForm />
    </div>
  );
};
