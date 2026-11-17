import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright E2E Test Configuration for KEEP
 */
export default defineConfig({
  testDir: './',
  fullyParallel: false,
  workers: 2,
  timeout: 60000,
  expect: {
    timeout: 15000,
  },
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on',
    screenshot: 'on',
  },
  webServer: {
    command: 'npx vite preview --port 3000 --host 0.0.0.0',
    cwd: path.resolve(__dirname, '../../frontend'),
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
});
