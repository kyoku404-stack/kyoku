import React from 'react';
import { ResetPasswordForm } from '@/features/auth/ResetPasswordForm';

export const ResetPasswordPage: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)] py-6">
      <ResetPasswordForm />
    </div>
  );
};
