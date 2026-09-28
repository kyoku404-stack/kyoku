import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, useTheme } from '@/context/ThemeContext';

const TestThemeConsumer: React.FC = () => {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();

  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <span data-testid="resolved-theme-value">{resolvedTheme}</span>
      <button data-testid="btn-dark" onClick={() => setTheme('dark')}>
        Set Dark
      </button>
      <button data-testid="btn-light" onClick={() => setTheme('light')}>
        Set Light
      </button>
      <button data-testid="btn-toggle" onClick={toggleTheme}>
        Toggle
      </button>
    </div>
  );
};

describe('ThemeContext & ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = '';
  });

  it('renders with default system theme and resolves to light by default in jsdom', () => {
    render(
      <ThemeProvider defaultTheme="system">
        <TestThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-value')).toHaveTextContent('system');
    expect(screen.getByTestId('resolved-theme-value')).toHaveTextContent('light');
    expect(document.documentElement.classList.contains('light')).toBe(true);
  });

  it('switches to dark theme when requested and updates documentElement class', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <TestThemeConsumer />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('btn-dark'));

    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem('keep_ui_theme')).toBe('dark');
  });

  it('toggles between dark and light themes', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <TestThemeConsumer />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('btn-toggle'));
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    fireEvent.click(screen.getByTestId('btn-toggle'));
    expect(document.documentElement.classList.contains('light')).toBe(true);
  });
});
