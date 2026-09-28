import React from 'react';
import { ThemeProvider } from '@/context/ThemeContext';

interface ProvidersProps {
  children: React.ReactNode;
}

export const Providers: React.FC<ProvidersProps> = ({ children }) => {
  return (
    <ThemeProvider defaultTheme="system">
      {children}
    </ThemeProvider>
  );
};
