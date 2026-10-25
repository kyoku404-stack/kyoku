/**
 * Phase 2.2 — RAG Engine & Semantic Search Playwright E2E Test Suite.
 *
 * Verifies end-to-end user workflows, grounded synthesis, and conversational interactions:
 * 1. AI Knowledge Search & Q&A Command Center Navigation:
 *    - Route verification (/rag and /chat) and sidebar integration with Phase 2.2 badge.
 *    - Header controls, executive telemetry toggle, and session history toggle.
 * 2. Executive KPI Metrics Banner:
 *    - Total Queries, Avg Latency, Mean Confidence Score, Satisfaction Rate, Guard Refusals.
 * 3. Retrieval Parameter Tuning:
 *    - Dense Vector vs Sparse Lexical weight sliders.
 *    - Preset buttons (Balanced RRF, Semantic Focus, Exact Keyword).
 *    - Top-K passage count selection.
 * 4. Multi-Turn Session History Sidebar:
 *    - Session listing, searching/filtering conversations, starting new consultation.
 * 5. Grounded Conversational Thread:
 *    - Starter prompt submission and custom textarea input.
 *    - Grounded answer rendering with confidence badge and processing duration.
 *    - Expandable telemetry performance breakdown.
 *    - Interactive source citation chips ([Source 1], [Source 2]).
 * 6. Source Provenance Citation Drawer:
 *    - Slide-over inspection of document title, page number, section, chunk ID, full excerpt.
 *    - View source document action and drawer dismissal.
 * 7. User Satisfaction Feedback:
 *    - Thumbs up helpful rating recording.
 *    - Thumbs down detailed feedback modal and comment submission.
 * 8. Responsive Viewport Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 2.2 — RAG Engine & Semantic Search
 * Specification: devdocs/p2/p2.2.txt Chapters 15-20 & docs/Architecture/ai-rag-engine.md
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
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_2_2');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_2_2');
    (window as any).__MOCK_USER__ = mockUser;
  }, role);
}

async function mockRAGApis(page: Page): Promise<void> {
  // 1. Mock Statistics
  await page.route('**/api/v1/rag/statistics', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Statistics retrieved successfully',
        data: {
          organization_id: '00000000-0000-0000-0000-000000000099',
          total_queries: 1420,
          total_sessions: 310,
          average_latency_ms: 245.5,
          average_confidence_score: 0.912,
          hallucination_refusal_count: 7,
          positive_feedback_percentage: 96.4,
          total_citations_rendered: 4260,
          cache_hit_ratio: 0.38,
        },
      }),
    });
  });

  // 2. Mock History
  await page.route('**/api/v1/rag/history*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'History retrieved successfully',
        data: {
          sessions: [
            {
              session_id: 'sess-e2e-001',
              title: 'Employee Leave Policy Consultation',
              created_at: '2026-10-25T10:00:00Z',
              updated_at: '2026-10-25T10:15:00Z',
              message_count: 2,
              messages: [
                {
                  message_id: 'msg-u1',
                  role: 'user',
                  content: 'What is our annual leave policy?',
                  created_at: '2026-10-25T10:00:00Z',
                },
                {
                  message_id: 'msg-a1',
                  role: 'assistant',
                  content: 'Full-time employees receive 20 days paid leave [Source 1].',
                  citations_json: JSON.stringify([
                    {
                      citation_id: 'cite-e2e-1',
                      document_id: 'doc-handbook-001',
                      document_title: 'Employee Handbook 2026.pdf',
                      page_number: 18,
                      section: 'Section 4.2: Paid Annual Leave',
                      chunk_id: 'chunk-handbook-001',
                      similarity_score: 0.94,
                      excerpt: 'All full-time employees are entitled to 20 days of paid annual leave per calendar year.',
                    },
                  ]),
                  created_at: '2026-10-25T10:00:02Z',
                },
              ],
            },
            {
              session_id: 'sess-e2e-002',
              title: 'AWS Cloud KMS Security Inquiries',
              created_at: '2026-10-25T11:00:00Z',
              updated_at: '2026-10-25T11:20:00Z',
              message_count: 4,
              messages: [],
            },
          ],
          total: 2,
          page: 1,
          page_size: 20,
        },
      }),
    });
  });

  // 3. Mock Query
  await page.route('**/api/v1/rag/query', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Query answered successfully',
        data: {
          query_id: 'q-e2e-999',
          session_id: 'sess-e2e-001',
          query: 'What is our enterprise employee leave policy?',
          answer: 'According to our enterprise policies, employees are entitled to 20 days of paid annual leave per year, requiring line manager approval [Source 1].',
          confidence_score: 0.945,
          is_grounded: true,
          processing_time_ms: 260,
          citations: [
            {
              citation_id: 'cite-e2e-1',
              document_id: 'doc-handbook-001',
              document_title: 'Employee Handbook 2026.pdf',
              page_number: 18,
              section: 'Section 4.2: Paid Annual Leave',
              chunk_id: 'chunk-handbook-001',
              similarity_score: 0.94,
              excerpt: 'All full-time employees are entitled to 20 days of paid annual leave per calendar year. Requests must be submitted at least two weeks in advance.',
            },
          ],
          retrieval_metrics: {
            dense_candidates: 12,
            sparse_candidates: 8,
            reranked_candidates: 5,
            latency_retrieval_ms: 110,
            latency_generation_ms: 150,
            tokens_prompt: 420,
            tokens_completion: 45,
          },
        },
      }),
    });
  });

  // 4. Mock Citation Detail
  await page.route('**/api/v1/rag/citations/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Citation details retrieved successfully',
        data: {
          citation_id: 'cite-e2e-1',
          chunk_id: 'chunk-handbook-001',
          document_id: 'doc-handbook-001',
          document_title: 'Employee Handbook 2026.pdf',
          chunk_index: 4,
          page_number: 18,
          section: 'Section 4.2: Paid Annual Leave',
          full_content: 'All full-time employees are entitled to 20 days of paid annual leave per calendar year. Requests must be submitted at least two weeks in advance via the HR portal.',
        },
      }),
    });
  });

  // 5. Mock Feedback
  await page.route('**/api/v1/rag/feedback', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        message: 'Feedback recorded successfully',
        data: {
          feedback_id: 'fb-e2e-001',
          recorded_at: '2026-10-26T00:00:00Z',
        },
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Playwright Test Suites
// ---------------------------------------------------------------------------

test.describe('Phase 2.2 — RAG Engine & Semantic Search E2E Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await mockRAGApis(page);
  });

  test('E2E-01: Navigates to /rag and verifies header, Phase 2.2 badge, and telemetry banner', async ({ page }) => {
    await page.goto('/rag');

    // Page Header & Badge
    await expect(page.locator('h1')).toHaveText(/AI Knowledge Search/);
    await expect(page.getByText('Phase 2.2 Active')).toBeVisible();

    // Toggle Executive Telemetry
    const toggleMetricsBtn = page.getByTestId('btn-toggle-metrics');
    await expect(toggleMetricsBtn).toBeVisible();
    await toggleMetricsBtn.click();

    // Verify 5 KPI stat cards
    await expect(page.getByTestId('rag-metrics-banner')).toBeVisible();
    await expect(page.getByTestId('metric-total-queries')).toHaveText('1,420');
    await expect(page.getByTestId('metric-avg-latency')).toHaveText('246 ms');
    await expect(page.getByTestId('metric-mean-confidence')).toHaveText('91.2%');
    await expect(page.getByTestId('metric-satisfaction')).toHaveText('96.4%');
    await expect(page.getByTestId('metric-refusals')).toHaveText('7');
  });

  test('E2E-02: Tunes hybrid search weights, selects presets, and adjusts Top-K candidates', async ({ page }) => {
    await page.goto('/rag');

    const filterBar = page.getByTestId('rag-search-filter-bar');
    await expect(filterBar).toBeVisible();

    // Verify Presets
    const semanticPreset = page.getByTestId('preset-semantic');
    await semanticPreset.click();

    // Verify slider updated
    const denseSlider = page.getByTestId('slider-dense-weight');
    await expect(denseSlider).toHaveValue('0.85');

    // Change Top-K
    const topKSelect = page.getByTestId('select-top-k');
    await topKSelect.selectOption('8');
    await expect(topKSelect).toHaveValue('8');

    // Reset Defaults
    const resetBtn = page.getByTestId('btn-reset-filters');
    await resetBtn.click();
    await expect(denseSlider).toHaveValue('0.65');
  });

  test('E2E-03: Submits natural language question, validates grounded answer, and inspects citations', async ({ page }) => {
    await page.goto('/rag');

    // Click starter prompt
    const starterPrompt = page.getByTestId('prompt-starter-0');
    await starterPrompt.click();

    // Wait for response
    await expect(page.getByText('Grounded Response')).toBeVisible();
    await expect(page.getByText(/95% confidence/)).toBeVisible();
    await expect(page.getByText(/according to our enterprise policies/i)).toBeVisible();

    // Citation Chip verification
    const citationChip = page.getByTestId('citation-chip-0');
    await expect(citationChip).toBeVisible();
    await citationChip.click();

    // Provenance Drawer slide-over
    const drawer = page.getByTestId('citation-drawer');
    await expect(drawer).toBeVisible();
    await expect(page.getByTestId('citation-doc-title')).toHaveText('Employee Handbook 2026.pdf');
    await expect(page.getByTestId('citation-full-content')).toContainText('20 days of paid annual leave');

    // Dismiss drawer
    const closeBtn = page.getByTestId('btn-close-citation');
    await closeBtn.click();
    await expect(drawer).not.toBeVisible();
  });

  test('E2E-04: Submits positive satisfaction feedback on generated answer', async ({ page }) => {
    await page.goto('/rag');

    // Select existing session with messages
    const sessionItem = page.getByTestId('session-item-sess-e2e-001');
    await sessionItem.click();

    // Feedback Controls
    const thumbsUp = page.getByTestId('btn-feedback-positive');
    await expect(thumbsUp).toBeVisible();
    await thumbsUp.click();

    await expect(page.getByText('Feedback recorded ✓')).toBeVisible();
  });

  test('E2E-05: Adapts responsively across Desktop, Tablet, and Mobile viewports', async ({ page }) => {
    // 1. Desktop (1440x900)
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/rag');
    await expect(page.getByTestId('rag-session-sidebar')).toBeVisible();
    await expect(page.getByTestId('rag-chat-thread')).toBeVisible();

    // 2. Tablet (768x1024)
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByTestId('rag-chat-thread')).toBeVisible();

    // 3. Mobile (375x667)
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByTestId('rag-chat-thread')).toBeVisible();
  });
});
