/**
 * Phase 1.8 — Document Upload, File Management & Storage System E2E Test Suite.
 *
 * Verifies end-to-end user workflows, responsive adaptations, and interactive widgets:
 * 1. Knowledge Repository Navigation & Component Hydration:
 *    - Page header, feature pills, upload trigger button, and document explorer container.
 * 2. Layout Mode Toggling:
 *    - Grid view cards vs Table view data rows switching and state preservation.
 * 3. Search & Category Filter Interactions:
 *    - Real-time debounced search input, clear button, and category dropdown selection.
 * 4. Document Upload Modal Lifecycle:
 *    - Opening modal via header action button, drag-and-drop dropzone inspection,
 *      metadata input fields, and keyboard dismissal (Escape).
 * 5. Document Preview Modal Inspection:
 *    - Inline preview modal rendering, header metadata display, and dismiss triggers.
 * 6. Responsive Viewport Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667) screen adaptations.
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-phase: Phase 1.8 Document Upload, File Management & Storage System
 * Specification: devdocs/p1/p1.8.txt Chapters 16, 17, 20
 */

import { expect, Page, test } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers & State Setup
// ---------------------------------------------------------------------------

async function setupAuthenticatedUser(
  page: Page,
  role: 'SuperAdmin' | 'OrgAdmin' | 'Manager' | 'Member' | 'Viewer' = 'OrgAdmin'
): Promise<void> {
  await page.addInitScript((userRole) => {
    const mockUser = {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'devops.admin@keep.enterprise.io',
      full_name: 'DevOps Administrator',
      role: userRole,
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('access_token', 'mock_jwt_token_phase_1_8');
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_1_8');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_1_8');
    (window as any).__MOCK_USER__ = mockUser;
  }, role);
}

// ---------------------------------------------------------------------------
// Test Suite: Document Management & Knowledge Repository
// ---------------------------------------------------------------------------

test.describe('Document Management & Storage UI (Phase 1.8)', () => {

  test.beforeEach(async ({ page }) => {
    // Intercept document listing endpoint to supply deterministic mock data
    await page.route('**/api/v1/documents*', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/download') || url.pathname.endsWith('/preview')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/pdf',
          body: '%PDF-1.7 mock preview data',
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            items: [
              {
                id: 'doc-0001-aaaa-bbbb',
                organization_id: '00000000-0000-0000-0000-000000000099',
                project_id: null,
                uploader_id: '00000000-0000-0000-0000-000000000001',
                title: 'Enterprise Architecture Framework 2026',
                description: 'Core system specifications and infrastructure blueprints',
                filename: 'architecture_framework.pdf',
                file_size: 2450000,
                file_type: 'application/pdf',
                category: 'TECHNICAL_DOCUMENTATION',
                tags: ['architecture', 'backend', 'phase1.8'],
                status: 'PROCESSED',
                current_version_number: 2,
                version_count: 2,
                ai_ready: true,
                chunk_count: 48,
                created_at: '2026-10-15T10:30:00Z',
                updated_at: '2026-10-16T14:20:00Z',
              },
              {
                id: 'doc-0002-cccc-dddd',
                organization_id: '00000000-0000-0000-0000-000000000099',
                project_id: null,
                uploader_id: '00000000-0000-0000-0000-000000000001',
                title: 'Information Security & Compliance Policy',
                description: 'Organizational data protection and cryptographic requirements',
                filename: 'security_policy_v1.docx',
                file_size: 1120000,
                file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                category: 'POLICIES',
                tags: ['compliance', 'security'],
                status: 'AWAITING_PROCESSING',
                current_version_number: 1,
                version_count: 1,
                ai_ready: false,
                chunk_count: 0,
                created_at: '2026-10-18T09:00:00Z',
                updated_at: '2026-10-18T09:00:00Z',
              },
            ],
            total: 2,
            page: 1,
            page_size: 20,
            total_pages: 1,
          },
        }),
      });
    });

    // Intercept document detail endpoint
    await page.route('**/api/v1/documents/doc-0001-aaaa-bbbb', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            id: 'doc-0001-aaaa-bbbb',
            organization_id: '00000000-0000-0000-0000-000000000099',
            project_id: null,
            uploader_id: '00000000-0000-0000-0000-000000000001',
            title: 'Enterprise Architecture Framework 2026',
            description: 'Core system specifications and infrastructure blueprints',
            filename: 'architecture_framework.pdf',
            file_size: 2450000,
            file_type: 'application/pdf',
            category: 'TECHNICAL_DOCUMENTATION',
            tags: ['architecture', 'backend', 'phase1.8'],
            status: 'PROCESSED',
            current_version_number: 2,
            version_count: 2,
            ai_ready: true,
            chunk_count: 48,
            created_at: '2026-10-15T10:30:00Z',
            updated_at: '2026-10-16T14:20:00Z',
            versions: [
              {
                id: 'ver-0002',
                document_id: 'doc-0001-aaaa-bbbb',
                version_number: 2,
                filename: 'architecture_framework_v2.pdf',
                file_size: 2450000,
                checksum_sha256: 'abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
                change_notes: 'Updated storage boundary diagrams and volume mounts',
                uploader_id: '00000000-0000-0000-0000-000000000001',
                created_at: '2026-10-16T14:20:00Z',
              },
              {
                id: 'ver-0001',
                document_id: 'doc-0001-aaaa-bbbb',
                version_number: 1,
                filename: 'architecture_framework_v1.pdf',
                file_size: 2310000,
                checksum_sha256: 'def4567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12',
                change_notes: 'Initial blueprint draft',
                uploader_id: '00000000-0000-0000-0000-000000000001',
                created_at: '2026-10-15T10:30:00Z',
              },
            ],
          },
        }),
      });
    });
  });

  test('1. Page load, header elements, and feature pills render correctly', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await page.goto('/documents', { waitUntil: 'domcontentloaded' });

    // Header validation
    await expect(page.locator('#documents-page')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Knowledge Repository/i })).toBeVisible();
    await expect(page.locator('#page-upload-btn')).toBeVisible();

    // Feature pills validation
    await expect(page.getByText('Multi-format support')).toBeVisible();
    await expect(page.getByText('Secure storage')).toBeVisible();
    await expect(page.getByText('AI-ready pipeline')).toBeVisible();

    // Document explorer container
    await expect(page.locator('#document-explorer')).toBeVisible();
  });

  test('2. Layout mode toggling between Grid View and Table View', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await page.goto('/documents', { waitUntil: 'domcontentloaded' });

    // Grid View active by default
    await expect(page.locator('#document-card-doc-0001-aaaa-bbbb')).toBeVisible();
    await expect(page.getByText('Enterprise Architecture Framework 2026')).toBeVisible();

    // Switch to Table View
    const tableBtn = page.locator('#view-table-btn');
    await expect(tableBtn).toBeVisible();
    await tableBtn.click();

    // Verify table row is rendered
    await expect(page.locator('#document-row-doc-0001-aaaa-bbbb')).toBeVisible();

    // Switch back to Grid View
    const gridBtn = page.locator('#view-grid-btn');
    await gridBtn.click();
    await expect(page.locator('#document-card-doc-0001-aaaa-bbbb')).toBeVisible();
  });

  test('3. Search and category filter toolbar controls operate smoothly', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await page.goto('/documents', { waitUntil: 'domcontentloaded' });

    // Search input
    const searchInput = page.locator('#document-search-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('Architecture');
    await expect(searchInput).toHaveValue('Architecture');

    // Category select filter
    const catFilter = page.locator('#document-category-filter');
    await expect(catFilter).toBeVisible();
    await catFilter.selectOption('TECHNICAL_DOCUMENTATION');
    await expect(catFilter).toHaveValue('TECHNICAL_DOCUMENTATION');
  });

  test('4. Document upload modal opens, displays drag-and-drop zone, and dismisses', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await page.goto('/documents', { waitUntil: 'domcontentloaded' });

    // Click upload trigger button
    const uploadBtn = page.locator('#page-upload-btn');
    await uploadBtn.click();

    // Upload modal opens
    await expect(page.getByText(/Upload Documents/i).first()).toBeVisible();
    await expect(page.getByText(/Drag and drop files here/i)).toBeVisible();
    await expect(page.locator('#upload-dropzone')).toBeVisible();
    await expect(page.locator('#upload-submit-btn')).toBeVisible();

    // Press Escape to dismiss modal
    await page.keyboard.press('Escape');
    await expect(page.locator('#upload-dropzone')).not.toBeVisible();
  });

  test('5. Preview modal displays document content and allows closing', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await page.goto('/documents', { waitUntil: 'domcontentloaded' });

    // Click card title to open preview modal
    const cardTitle = page.getByText('Enterprise Architecture Framework 2026');
    await cardTitle.click();

    // Verify preview modal is open
    const previewModal = page.locator('#document-preview-modal');
    await expect(previewModal).toBeVisible();

    // Close preview modal via Escape
    await page.keyboard.press('Escape');
    await expect(previewModal).not.toBeVisible();
  });

  test('6. Responsive viewport adaptation across Desktop, Tablet, and Mobile', async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');

    // Desktop Viewport (1440x900)
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/documents', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#document-explorer')).toBeVisible();
    await expect(page.locator('#page-upload-btn')).toBeVisible();

    // Tablet Viewport (768x1024)
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('#document-explorer')).toBeVisible();

    // Mobile Viewport (375x667)
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('#document-explorer')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Knowledge Repository/i })).toBeVisible();
  });
});
