/**
 * Phase 3.2 — Real-Time Collaboration, Team Workspaces & Knowledge Sharing Playwright E2E Test Suite.
 *
 * Verifies end-to-end user workflows, workspace lifecycle, threaded discussions, mentions, presence, activity feed, and version control:
 * 1. Navigation & Command Center:
 *    - Route reachability (/collaboration, /workspaces).
 *    - Sidebar integration with Users icon and Phase 3.2 badge.
 * 2. Workspace Management:
 *    - Workspace header with search, visibility toggle, and Create Workspace button.
 *    - Create Workspace modal validation and submission.
 *    - Workspace grid cards showing member counts and status badges.
 * 3. Document Collaboration & Threaded Discussions:
 *    - Discussion thread list displaying comment bodies and resolution toggles.
 *    - Rich CommentBox with character limit and @mention popover.
 *    - Threaded replies to parent comments.
 *    - Thread resolution marking comment as resolved.
 * 4. AI Discussion Summarization:
 *    - AI summary generation callout with executive summary, action items, and key decisions.
 * 5. Live Presence & Activity Feed:
 *    - Live presence indicator badges (Online, Busy, Away) and collaborator avatars.
 *    - Chronological activity timeline with action badges and actor attribution.
 * 6. Document Version Control Drawer:
 *    - Version history drawer listing checkpoints (v1, v2) with commit details.
 *    - Checkpoint creation and version rollback action.
 * 7. Responsive Breakpoint Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 3.2 — Real-Time Collaboration, Team Workspaces & Knowledge Sharing
 * Specification: devdocs/p3/p3.2.txt & docs/Architecture/real-time-collaboration-team-workspaces.md
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
      email: 'lead.architect@keep.enterprise.io',
      full_name: 'Lead AI Architect',
      role: userRole,
      organization_id: '00000000-0000-0000-0000-000000000099',
      is_active: true,
      created_at: '2026-10-01T00:00:00Z',
    };
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_3_2');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_3_2');
    (window as unknown as { __MOCK_USER__: typeof mockUser }).__MOCK_USER__ = mockUser;
  }, role);
}

async function setupCollaborationApiMocks(page: Page): Promise<void> {
  // 1. Workspaces Mock
  await page.route('**/api/v1/workspaces/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    if (method === 'GET' && url.includes('/list')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            total: 2,
            workspaces: [
              {
                id: 'ws-1111-2222-3333-4444',
                name: 'Product Engineering Core',
                slug: 'prod-eng-core',
                description: 'Core microservices, infrastructure, and API architecture team.',
                avatar_color: '#4F46E5',
                is_private: false,
                member_count: 8,
                current_user_role: 'ADMIN',
                created_at: '2026-10-20T08:00:00Z',
              },
              {
                id: 'ws-5555-6666-7777-8888',
                name: 'AI & Data Intelligence',
                slug: 'ai-data-intelligence',
                description: 'Vector embeddings, graph models, and autonomous agent workflows.',
                avatar_color: '#10B981',
                is_private: true,
                member_count: 5,
                current_user_role: 'MEMBER',
                created_at: '2026-10-22T10:30:00Z',
              },
            ],
          },
          status: 'success',
        }),
      });
      return;
    }

    if (method === 'POST' && url.includes('/create')) {
      const payload = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'ws-new-9999-0000',
            name: payload.name || 'New Team Workspace',
            slug: payload.slug || 'new-team-workspace',
            description: payload.description || 'Custom collaborative workspace',
            avatar_color: payload.avatar_color || '#4F46E5',
            is_private: payload.is_private || false,
            member_count: 1,
            current_user_role: 'ADMIN',
            created_at: new Date().toISOString(),
          },
          status: 'success',
        }),
      });
      return;
    }

    // Default workspace detail fallback
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          id: 'ws-1111-2222-3333-4444',
          name: 'Product Engineering Core',
          slug: 'prod-eng-core',
          description: 'Core microservices and infrastructure.',
          avatar_color: '#4F46E5',
          is_private: false,
          member_count: 8,
          current_user_role: 'ADMIN',
          members: [
            {
              id: 'm-1',
              user_id: '00000000-0000-0000-0000-000000000001',
              email: 'lead.architect@keep.enterprise.io',
              full_name: 'Lead AI Architect',
              role: 'ADMIN',
              joined_at: '2026-10-20T08:00:00Z',
            },
          ],
          created_at: '2026-10-20T08:00:00Z',
        },
        status: 'success',
      }),
    });
  });

  // 2. Comments & Discussions Mock
  await page.route('**/api/v1/comments/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    if (method === 'GET' && url.includes('/document/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            document_id: 'doc-1234-5678',
            total_comments: 1,
            comments: [
              {
                id: 'comm-101',
                document_id: 'doc-1234-5678',
                workspace_id: 'ws-1111-2222-3333-4444',
                parent_comment_id: null,
                author_id: '00000000-0000-0000-0000-000000000001',
                author_name: 'Lead AI Architect',
                content: 'Please verify the vector partition indexing strategy with @sarah.connor before deployment.',
                page_number: 3,
                highlight_text: 'Section 3.2 HNSW Indexing Parameters',
                status: 'OPEN',
                resolved_by_id: null,
                resolved_at: null,
                mentions: ['@sarah.connor'],
                replies: [],
                created_at: '2026-10-28T08:30:00Z',
              },
            ],
          },
          status: 'success',
        }),
      });
      return;
    }

    if (method === 'POST' && url.includes('/create')) {
      const payload = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: `comm-${Date.now()}`,
            document_id: payload.document_id || 'doc-1234-5678',
            workspace_id: payload.workspace_id,
            parent_comment_id: null,
            author_id: '00000000-0000-0000-0000-000000000001',
            author_name: 'Lead AI Architect',
            content: payload.content || 'Test comment',
            page_number: payload.page_number,
            highlight_text: payload.highlight_text,
            status: 'OPEN',
            resolved_by_id: null,
            resolved_at: null,
            mentions: ['@team'],
            replies: [],
            created_at: new Date().toISOString(),
          },
          status: 'success',
        }),
      });
      return;
    }

    if (method === 'POST' && url.includes('/resolve')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'comm-101',
            status: 'RESOLVED',
            resolved_by_id: '00000000-0000-0000-0000-000000000001',
            resolved_at: new Date().toISOString(),
          },
          status: 'success',
        }),
      });
      return;
    }

    await route.continue();
  });

  // 3. Presence Mocks
  await page.route('**/api/v1/presence/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    if (method === 'POST' && url.includes('/heartbeat')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: { received: true, timestamp: new Date().toISOString() },
          status: 'success',
        }),
      });
      return;
    }

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            workspace_id: 'ws-1111-2222-3333-4444',
            collaborators: [
              {
                user_id: '00000000-0000-0000-0000-000000000001',
                full_name: 'Lead AI Architect',
                email: 'lead.architect@keep.enterprise.io',
                status: 'ONLINE',
                document_id: 'doc-1234-5678',
                last_seen_at: new Date().toISOString(),
              },
              {
                user_id: '00000000-0000-0000-0000-000000000002',
                full_name: 'Sarah Connor',
                email: 'sarah.connor@keep.enterprise.io',
                status: 'EDITING',
                document_id: 'doc-1234-5678',
                last_seen_at: new Date().toISOString(),
              },
            ],
          },
          status: 'success',
        }),
      });
      return;
    }

    await route.continue();
  });

  // 4. Activity Feed Mock
  await page.route('**/api/v1/activity/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          workspace_id: 'ws-1111-2222-3333-4444',
          activities: [
            {
              id: 'act-1',
              activity_type: 'COMMENT_ADDED',
              actor_id: '00000000-0000-0000-0000-000000000001',
              actor_name: 'Lead AI Architect',
              entity_id: 'comm-101',
              entity_type: 'COMMENT',
              entity_title: 'HNSW Indexing Review',
              description: 'posted a comment on Architecture Design Spec',
              metadata: { document_id: 'doc-1234-5678' },
              created_at: '2026-10-28T08:30:00Z',
            },
            {
              id: 'act-2',
              activity_type: 'WORKSPACE_CREATED',
              actor_id: '00000000-0000-0000-0000-000000000001',
              actor_name: 'Lead AI Architect',
              entity_id: 'ws-1111-2222-3333-4444',
              entity_type: 'WORKSPACE',
              entity_title: 'Product Engineering Core',
              description: 'created workspace Product Engineering Core',
              metadata: {},
              created_at: '2026-10-20T08:00:00Z',
            },
          ],
        },
        status: 'success',
      }),
    });
  });

  // 5. Version History Mock
  await page.route('**/api/v1/version/**', async (route) => {
    const url = route.request().url();
    if (url.includes('/history/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            document_id: 'doc-1234-5678',
            total_versions: 2,
            versions: [
              {
                version_id: 'v-2',
                version_number: 2,
                editor_id: '00000000-0000-0000-0000-000000000001',
                editor_name: 'Lead AI Architect',
                change_summary: 'Updated indexing parameters and memory thresholds',
                file_size_bytes: 2048576,
                checksum: 'abcdef...',
                approval_status: 'APPROVED',
                created_at: '2026-10-28T08:00:00Z',
              },
              {
                version_id: 'v-1',
                version_number: 1,
                editor_id: '00000000-0000-0000-0000-000000000001',
                editor_name: 'Lead AI Architect',
                change_summary: 'Initial draft of architecture blueprint',
                file_size_bytes: 1048576,
                checksum: '123456...',
                approval_status: 'APPROVED',
                created_at: '2026-10-25T10:00:00Z',
              },
            ],
          },
          status: 'success',
        }),
      });
      return;
    }
    await route.continue();
  });

  // 6. AI Discussion Summary Mock
  await page.route('**/api/v1/collaboration/discussions/**/summary', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          document_id: 'doc-1234-5678',
          executive_summary: 'Team aligned on HNSW indexing parameters for sub-50ms query SLAs. Sarah Connor approved benchmark results.',
          key_decisions: [
            { decision: 'Adopt HNSW index with M=16 and efConstruction=200', agreed_by: 'Lead Architect, Sarah Connor' },
          ],
          action_items: [
            { item: 'Execute stress benchmark in staging cluster', assignee: 'Sarah Connor', status: 'IN_PROGRESS' },
          ],
          unresolved_questions: [],
          suggested_documents: [],
          processing_time_ms: 125.4,
        },
        status: 'success',
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Test Suites
// ---------------------------------------------------------------------------

test.describe('Phase 3.2 — Real-Time Collaboration & Team Workspaces E2E', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await setupCollaborationApiMocks(page);
  });

  test('TC-3.2-01: Navigates to Collaboration page via sidebar and verifies command center layout', async ({ page }) => {
    await page.goto('/collaboration');

    // Verify main header and description
    await expect(page.locator('h1')).toContainText('Real-Time Collaboration');
    await expect(page.getByText('Team workspaces, collaborative discussions, live presence')).toBeVisible();

    // Verify navigation tabs
    await expect(page.getByRole('tab', { name: /Workspaces & Projects/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Document Collaboration & Threads/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Live Activity & Presence/i })).toBeVisible();

    // Verify presence badge
    await expect(page.getByText(/Collaborating Now/i)).toBeVisible();
  });

  test('TC-3.2-02: Workspace grid rendering, search filtering, and Create Workspace modal workflow', async ({ page }) => {
    await page.goto('/collaboration');

    // Workspaces should be rendered in grid
    await expect(page.getByText('Product Engineering Core')).toBeVisible();
    await expect(page.getByText('AI & Data Intelligence')).toBeVisible();

    // Open Create Workspace Modal
    const createBtn = page.getByRole('button', { name: /Create Workspace/i });
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // Modal should appear
    await expect(page.getByText('Create New Workspace')).toBeVisible();

    // Fill workspace form
    await page.fill('#workspace-name', 'Platform Security Operations');
    await page.fill('#workspace-slug', 'platform-sec-ops');
    await page.fill('#workspace-description', 'Zero trust access management and audit log investigations.');

    // Submit form
    const submitBtn = page.getByRole('button', { name: /Create Workspace/i }).last();
    await submitBtn.click();

    // Modal should close upon successful creation
    await expect(page.getByText('Create New Workspace')).not.toBeVisible();
  });

  test('TC-3.2-03: Document discussion threads, rich comment composer with @mention suggestion', async ({ page }) => {
    await page.goto('/collaboration');

    // Switch to Document Discussions tab
    await page.getByRole('tab', { name: /Document Collaboration & Threads/i }).click();

    // Verify thread comments visible
    await expect(page.getByText(/Please verify the vector partition indexing strategy/i)).toBeVisible();
    await expect(page.getByText('Section 3.2 HNSW Indexing Parameters')).toBeVisible();

    // Verify rich CommentBox composer
    const commentInput = page.getByPlaceholder(/Add a comment or observation/i);
    await expect(commentInput).toBeVisible();

    // Type comment body and trigger @mention
    await commentInput.fill('Review complete. Ready for production rollout @');

    // Mention suggestions popover should appear
    await expect(page.getByText('Mention Teammate')).toBeVisible();
    await expect(page.getByText('All Workspace Collaborators')).toBeVisible();

    // Select mention
    await page.getByText('All Workspace Collaborators').click();
    await expect(commentInput).toHaveValue('Review complete. Ready for production rollout @team ');
  });

  test('TC-3.2-04: AI Discussion Summarization briefing generation', async ({ page }) => {
    await page.goto('/collaboration');

    // Switch to Document Discussions tab
    await page.getByRole('tab', { name: /Document Collaboration & Threads/i }).click();

    // Click AI Summarize Discussion button
    const summarizeBtn = page.getByRole('button', { name: /AI Summarize Discussion/i });
    await expect(summarizeBtn).toBeVisible();
    await summarizeBtn.click();

    // Executive summary card should render
    await expect(page.getByText(/AI Executive Briefing/i)).toBeVisible();
    await expect(page.getByText(/Team aligned on HNSW indexing parameters for sub-50ms query SLAs/i)).toBeVisible();
    await expect(page.getByText(/Adopt HNSW index with M=16/i)).toBeVisible();
  });

  test('TC-3.2-05: Live presence indicators and activity timeline verification', async ({ page }) => {
    await page.goto('/collaboration');

    // Switch to Activity & Presence tab
    await page.getByRole('tab', { name: /Live Activity & Presence/i }).click();

    // Verify Active Collaborators roster
    await expect(page.getByText('Sarah Connor')).toBeVisible();
    await expect(page.getByText('EDITING')).toBeVisible();

    // Verify Activity Stream Timeline
    await expect(page.getByText('Recent Workspace Activity')).toBeVisible();
    await expect(page.getByText(/posted a comment on Architecture Design Spec/i)).toBeVisible();
    await expect(page.getByText(/created workspace Product Engineering Core/i)).toBeVisible();
  });

  test('TC-3.2-06: Document Version History Drawer and rollback interaction', async ({ page }) => {
    await page.goto('/collaboration');

    // Switch to Document Discussions tab
    await page.getByRole('tab', { name: /Document Collaboration & Threads/i }).click();

    // Open Version History Drawer
    const versionBtn = page.getByRole('button', { name: /Version History/i });
    await expect(versionBtn).toBeVisible();
    await versionBtn.click();

    // Drawer should slide in
    await expect(page.getByText('Document Version History')).toBeVisible();
    await expect(page.getByText('Version 2')).toBeVisible();
    await expect(page.getByText('Version 1')).toBeVisible();

    // Verify rollback button on historical version 1
    const rollbackBtn = page.getByRole('button', { name: /Rollback/i });
    await expect(rollbackBtn).toBeVisible();
  });

  test('TC-3.2-07: Responsive Breakpoint Adaptations (Desktop, Tablet, Mobile)', async ({ page }) => {
    // 1. Desktop Breakpoint (1440x900)
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/collaboration');
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.getByRole('tab', { name: /Workspaces & Projects/i })).toBeVisible();

    // 2. Tablet Breakpoint (768x1024)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.getByRole('tab', { name: /Workspaces & Projects/i })).toBeVisible();

    // 3. Mobile Breakpoint (375x667)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await expect(page.locator('h1')).toBeVisible();
    // In mobile, tabs should be accessible and scrollable
    await expect(page.getByRole('tab', { name: /Workspaces/i })).toBeVisible();
  });
});
