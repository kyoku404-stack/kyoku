import React from 'react';
import { RegisterForm } from '@/features/auth/RegisterForm';

export const RegisterPage: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-12rem)] py-6">
      <RegisterForm />
    </div>
  );
};
