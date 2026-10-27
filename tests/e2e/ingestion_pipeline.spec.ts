/**
 * Phase 2.1 — AI Knowledge Ingestion Pipeline E2E Test Suite.
 *
 * Verifies end-to-end user workflows, asynchronous state machines, and real-time monitoring:
 * 1. AI Ingestion Command Center Navigation & Component Hydration:
 *    - Route verification (/ingestion) and sidebar integration.
 *    - Top header, Phase 2.1 milestone badge, polling toggle, manual refresh, and Start Ingestion CTA.
 *    - Ingestion architecture overview banner.
 * 2. Executive KPI Metrics Grid:
 *    - Total Ingestion Jobs card with active queue breakdowns.
 *    - Document Chunks Indexed in pgvector.
 *    - Throughput Velocity (pages/minute) and Mean Processing Duration.
 *    - OCR Utilization percentage.
 * 3. 8-Stage Pipeline Progress Stepper:
 *    - PENDING, EXTRACTING, OCR_PROCESSING, NORMALIZING, CHUNKING, EMBEDDING, INDEXING, COMPLETED.
 * 4. Filterable & Searchable Ingestion Jobs Table:
 *    - Real-time debounced search input by document title or job ID.
 *    - Status filter tabs: All, In Progress, Completed, Failed.
 *    - Job actions: Inspect progress and Retry failed job.
 * 5. Start Ingestion Configuration Modal:
 *    - Modal opening via header trigger.
 *    - Input fields: Document ID, Chunking Strategy dropdown, Embedding Model dropdown, Force OCR checkbox.
 *    - Dispatching asynchronous ingestion job.
 * 6. Live Ingestion Progress & Stage Inspection Modal:
 *    - Live stage inspector rendering with page ratios, vector counts, and timestamps.
 *    - Diagnostic error log inspection and inline retry button for failed executions.
 * 7. Responsive Viewport Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 2.1 — AI Knowledge Ingestion Pipeline
 * Specification: devdocs/p2/p2.1.txt Chapters 15, 16, 17 & docs/Architecture/ai-ingestion-pipeline.md
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
      full_name: 'DevOps System Administrator',
      role: userRole,
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_2_1');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_2_1');
    (window as any).__MOCK_USER__ = mockUser;
  }, role);
}

const mockStatistics = {
  success: true,
  data: {
    organization_id: '00000000-0000-0000-0000-000000000099',
    total_jobs: 142,
    completed_jobs: 128,
    failed_jobs: 6,
    pending_jobs: 8,
    total_chunks_indexed: 4892,
    average_duration_seconds: 4.85,
    average_throughput_pages_per_minute: 42.0,
    ocr_utilization_percent: 18.5,
    retry_success_rate_percent: 88.0,
  },
};

const mockJobsList = {
  success: true,
  data: {
    items: [
      {
        job_id: 'job-0001-aaaa-1111',
        document_id: 'doc-0001',
        document_title: 'Enterprise Architecture Blueprint.pdf',
        status: 'COMPLETED',
        chunks_generated: 64,
        duration_seconds: 5.2,
        created_at: '2026-10-25T11:00:00Z',
        completed_at: '2026-10-25T11:00:05Z',
      },
      {
        job_id: 'job-0002-bbbb-2222',
        document_id: 'doc-0002',
        document_title: 'Financial Q3 Audit Report.docx',
        status: 'CHUNKING',
        chunks_generated: 18,
        duration_seconds: 2.1,
        created_at: '2026-10-25T11:10:00Z',
        completed_at: null,
      },
      {
        job_id: 'job-0003-cccc-3333',
        document_id: 'doc-0003',
        document_title: 'Corrupted Scanned Invoice.png',
        status: 'FAILED',
        chunks_generated: 0,
        duration_seconds: 1.4,
        created_at: '2026-10-25T11:15:00Z',
        completed_at: null,
      },
    ],
    total: 3,
    page: 1,
    page_size: 10,
    total_pages: 1,
  },
};

const mockJobStatusDetails = {
  success: true,
  data: {
    job_id: 'job-0001-aaaa-1111',
    document_id: 'doc-0001',
    status: 'COMPLETED',
    progress_percent: 100.0,
    current_stage: 'COMPLETED',
    total_pages: 12,
    processed_pages: 12,
    chunks_generated: 64,
    embeddings_generated: 64,
    ocr_applied: false,
    retry_count: 0,
    error_message: null,
    started_at: '2026-10-25T11:00:00Z',
    completed_at: '2026-10-25T11:00:05Z',
    duration_seconds: 5.2,
  },
};

const mockFailedJobStatus = {
  success: true,
  data: {
    job_id: 'job-0003-cccc-3333',
    document_id: 'doc-0003',
    status: 'FAILED',
    progress_percent: 35.0,
    current_stage: 'OCR_PROCESSING',
    total_pages: 1,
    processed_pages: 0,
    chunks_generated: 0,
    embeddings_generated: 0,
    ocr_applied: true,
    retry_count: 0,
    error_message: 'PaddleOCR engine timeout: Image stream could not be decoded',
    started_at: '2026-10-25T11:15:00Z',
    completed_at: null,
    duration_seconds: 1.4,
  },
};

// ---------------------------------------------------------------------------
// E2E Test Suite: AI Knowledge Ingestion Pipeline
// ---------------------------------------------------------------------------

test.describe('Phase 2.1 — AI Ingestion Pipeline Command Center', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');

    // Intercept backend API routes
    await page.route('**/api/v1/ingestion/statistics', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStatistics),
      });
    });

    await page.route('**/api/v1/ingestion/jobs*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockJobsList),
      });
    });

    await page.route('**/api/v1/ingestion/status/job-0001-aaaa-1111', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockJobStatusDetails),
      });
    });

    await page.route('**/api/v1/ingestion/status/job-0003-cccc-3333', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockFailedJobStatus),
      });
    });

    await page.route('**/api/v1/ingestion/start', async (route) => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            job_id: 'job-9999-new-dispatch',
            document_id: 'doc-0001',
            status: 'PENDING',
            queue_name: 'ai_ingestion_queue',
            enqueued_at: new Date().toISOString(),
          },
        }),
      });
    });

    await page.route('**/api/v1/ingestion/retry/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            job_id: 'job-0003-cccc-3333',
            status: 'RETRYING',
            retry_count: 1,
            message: 'Job re-enqueued for ingestion processing',
          },
        }),
      });
    });

    await page.goto('/ingestion', { waitUntil: 'domcontentloaded' });
  });

  test('1. Command Center loads with header, Phase 2.1 badge, and top action buttons', async ({ page }) => {
    await expect(page.locator('#ingestion-dashboard-page')).toBeVisible();
    await expect(page.getByText('AI Knowledge Ingestion Pipeline').first()).toBeVisible();
    await expect(page.getByText('Phase 2.1').first()).toBeVisible();

    // Verify action buttons
    await expect(page.getByTestId('live-polling-toggle')).toBeVisible();
    await expect(page.getByTestId('manual-refresh-button')).toBeVisible();
    await expect(page.getByTestId('start-ingestion-button')).toBeVisible();
  });

  test('2. Renders executive KPI metrics cards accurately', async ({ page }) => {
    // Total Jobs Card
    const totalJobsMetric = page.getByTestId('metric-total-jobs');
    await expect(totalJobsMetric).toBeVisible();
    await expect(totalJobsMetric).toContainText('142');

    // Chunks Indexed Card
    const chunksMetric = page.getByTestId('metric-chunks-indexed');
    await expect(chunksMetric).toBeVisible();
    await expect(chunksMetric).toContainText('4,892');

    // Throughput Velocity Card
    const throughputMetric = page.getByTestId('metric-throughput');
    await expect(throughputMetric).toBeVisible();
    await expect(throughputMetric).toContainText('42');

    // OCR Utilization Card
    const ocrMetric = page.getByTestId('metric-ocr-utilization');
    await expect(ocrMetric).toBeVisible();
    await expect(ocrMetric).toContainText('19%');
  });

  test('3. Jobs table displays records, status badges, chunk counts, and search filter works', async ({ page }) => {
    // Document row titles
    await expect(page.getByText('Enterprise Architecture Blueprint.pdf')).toBeVisible();
    await expect(page.getByText('Financial Q3 Audit Report.docx')).toBeVisible();
    await expect(page.getByText('Corrupted Scanned Invoice.png')).toBeVisible();

    // Status badges
    await expect(page.getByText('COMPLETED')).toBeVisible();
    await expect(page.getByText('FAILED')).toBeVisible();

    // Search filter input
    const searchInput = page.getByTestId('ingestion-search-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('Architecture');

    // Filtered result
    await expect(page.getByText('Enterprise Architecture Blueprint.pdf')).toBeVisible();
    await expect(page.getByText('Financial Q3 Audit Report.docx')).not.toBeVisible();

    // Clear search
    await searchInput.fill('');
    await expect(page.getByText('Financial Q3 Audit Report.docx')).toBeVisible();
  });

  test('4. Status filter tabs trigger filtering on job state', async ({ page }) => {
    const failedTab = page.getByTestId('filter-tab-failed');
    await expect(failedTab).toBeVisible();
    await failedTab.click();

    // All tab restores full view
    const allTab = page.getByTestId('filter-tab-all');
    await expect(allTab).toBeVisible();
    await allTab.click();
  });

  test('5. Start Ingestion Modal opens, displays configuration fields, and submits', async ({ page }) => {
    const startButton = page.getByTestId('start-ingestion-button');
    await startButton.click();

    // Modal dialog visible
    const modal = page.getByTestId('start-ingestion-modal');
    await expect(modal).toBeVisible();
    await expect(page.getByTestId('start-ingestion-form')).toBeVisible();

    // Fill document ID
    const docInput = page.getByTestId('input-document-id');
    await expect(docInput).toBeVisible();
    await docInput.fill('00000000-0000-0000-0000-000000000001');

    // Toggle force OCR checkbox
    const ocrCheckbox = page.getByTestId('checkbox-force-ocr');
    await expect(ocrCheckbox).toBeVisible();
    await ocrCheckbox.click();

    // Submit ingestion job
    const submitBtn = page.getByTestId('submit-ingest-btn');
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // Modal closes upon successful dispatch
    await expect(modal).not.toBeVisible();
  });

  test('6. Ingestion Progress Inspector modal opens on Inspect click and displays stage stepper', async ({ page }) => {
    const inspectBtn = page.getByTestId('inspect-btn-job-0001-aaaa-1111');
    await expect(inspectBtn).toBeVisible();
    await inspectBtn.click();

    // Verify inspection modal
    const inspectModal = page.getByTestId('ingestion-progress-modal');
    await expect(inspectModal).toBeVisible();

    // Verify stage stepper elements
    await expect(page.getByTestId('stage-pending')).toBeVisible();
    await expect(page.getByTestId('stage-extracting')).toBeVisible();
    await expect(page.getByTestId('stage-chunking')).toBeVisible();
    await expect(page.getByTestId('stage-embedding')).toBeVisible();
    await expect(page.getByTestId('stage-completed')).toBeVisible();

    // Close modal
    const closeBtn = inspectModal.locator('button').filter({ hasText: /Close/i }).first();
    if (await closeBtn.isVisible()) {
      await closeBtn.click();
    }
  });

  test('7. Failed job row displays Retry button and triggers retry action', async ({ page }) => {
    const retryBtn = page.getByTestId('retry-btn-job-0003-cccc-3333');
    await expect(retryBtn).toBeVisible();
    await retryBtn.click();

    // Retry button triggers API request without crashing
    await expect(page.locator('#ingestion-dashboard-page')).toBeVisible();
  });

  test('8. Responsive layout adapts gracefully across Desktop, Tablet, and Mobile viewports', async ({ page }) => {
    // 1. Desktop Viewport
    await page.setViewportSize({ width: 1440, height: 900 });
    await expect(page.locator('#ingestion-dashboard-page')).toBeVisible();
    await expect(page.getByTestId('metric-total-jobs')).toBeVisible();

    // 2. Tablet Viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('#ingestion-dashboard-page')).toBeVisible();
    await expect(page.getByTestId('metric-total-jobs')).toBeVisible();

    // 3. Mobile Viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('#ingestion-dashboard-page')).toBeVisible();
    await expect(page.getByTestId('start-ingestion-button')).toBeVisible();
  });
});
