import { test, expect } from '@playwright/test';

test.describe('KEEP Platform Smoke Tests', () => {
  test('Landing Page loads with correct title and navigation elements', async ({ page }) => {
    await page.goto('/');
    
    // Expect page title or header
    await expect(page).toHaveTitle(/KEEP/i);
    
    // Expect navigation items
    const header = page.locator('header');
    await expect(header).toBeVisible();
  });

  test('Health check page renders system telemetry status', async ({ page }) => {
    await page.goto('/health');
    
    // Check for health indicators
    await expect(page.locator('text=System Health')).toBeVisible();
  });
});
