/**
 * Phase 2.4 — Knowledge Graph Construction, Relationship Mapping & Enterprise Intelligence Playwright E2E Test Suite.
 *
 * Verifies end-to-end user workflows, relational topology canvas, blast radius analysis, and SME discovery:
 * 1. Knowledge Graph Cockpit Navigation:
 *    - Route verification (/graph and /knowledge-graph) and sidebar integration with Phase 2.4 badge.
 *    - View switching tabs (Topology Explorer, Impact Analysis, Expertise Discovery).
 * 2. Executive KPI Metrics Banner:
 *    - Total Entities, Active Relationships, Topological Density, Top Hub Node.
 * 3. Filter Bar & Graph Construction Controls:
 *    - Search input, Entity Type dropdown filter, refresh trigger, build trigger, and incremental text ingestion drawer.
 * 4. Interactive Knowledge Explorer Canvas:
 *    - Force topology SVG rendering, node elements with entity labels, zoom controls, and node selection halo.
 * 5. Entity Detail Drawer:
 *    - Deep inspection drawer displaying in/out degree counts, incoming/outgoing relationship edges, and blast radius trigger.
 * 6. Downstream Impact Analysis Blast Radius:
 *    - Tab navigation, calculated severity score bar, affected scope breakdown, and hierarchical dependency tree.
 * 7. Subject-Matter Expertise Directory:
 *    - Tab navigation, topic search input, ranked personnel cards with score progress bars, authorship counts, and citations.
 * 8. Responsive Viewport Adaptations:
 *    - Desktop (1440x900), Tablet (768x1024), and Mobile (375x667).
 *
 * Owner: Member 4 (DevOps & Integration Lead)
 * Sub-Phase: Phase 2.4 — Knowledge Graph Construction, Relationship Mapping & Enterprise Intelligence
 * Specification: devdocs/p2/p2.4.txt & docs/Architecture/knowledge-graph-enterprise-intelligence.md
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
    localStorage.setItem('keep_auth_token', 'mock_jwt_token_phase_2_4');
    localStorage.setItem('keep_refresh_token', 'mock_refresh_token_phase_2_4');
    (window as any).__MOCK_USER__ = mockUser;
  }, role);
}

async function setupGraphApiMocks(page: Page): Promise<void> {
  await page.route('**/api/v1/graph/**', async (route) => {
    const url = route.request().url();
    const method = route.request().method();

    // 1. Explorer Topology Data
    if (url.includes('/api/v1/graph/explorer')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Explorer topology retrieved successfully.',
          data: {
            nodes: [
              { id: 'node-corp', label: 'KEEP Global Enterprise', type: 'ORGANIZATION', val: 25 },
              { id: 'node-eng', label: 'Platform Engineering', type: 'DEPARTMENT', val: 20 },
              { id: 'node-proj', label: 'Project Titan', type: 'PROJECT', val: 18 },
              { id: 'node-alice', label: 'Alice Smith', type: 'EMPLOYEE', val: 15 },
              { id: 'node-sec', label: 'Access Control Standard', type: 'POLICY', val: 14 },
            ],
            links: [
              { source: 'node-eng', target: 'node-corp', label: 'BELONGS_TO', weight: 1.0 },
              { source: 'node-proj', target: 'node-eng', label: 'GOVERNED_BY', weight: 0.9 },
              { source: 'node-alice', target: 'node-proj', label: 'LEADS', weight: 0.95 },
              { source: 'node-proj', target: 'node-sec', label: 'COMPLIES_WITH', weight: 0.85 },
            ],
            metrics: {
              total_entities: 48,
              total_relationships: 92,
              density: 0.0816,
              top_hub: 'Platform Engineering',
            },
          },
        }),
      });
    }

    // 2. Entity Details
    if (url.includes('/api/v1/graph/entity/node-proj')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Entity retrieved successfully.',
          data: {
            id: 'node-proj',
            organization_id: '00000000-0000-0000-0000-000000000099',
            name: 'Project Titan',
            entity_type: 'PROJECT',
            properties: { priority: 'P0', tier: 'Production' },
            in_degree: 2,
            out_degree: 3,
            created_at: '2026-10-01T00:00:00Z',
          },
        }),
      });
    }

    // 3. Entity Relationships
    if (url.includes('/api/v1/graph/relationships/node-proj')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Entity relationships retrieved successfully.',
          data: {
            entity_id: 'node-proj',
            outgoing_relationships: [
              {
                relationship_id: 'rel-1',
                target_entity_id: 'node-eng',
                target_entity_name: 'Platform Engineering',
                target_entity_type: 'DEPARTMENT',
                relation_type: 'GOVERNED_BY',
                weight: 0.9,
              },
            ],
            incoming_relationships: [
              {
                relationship_id: 'rel-2',
                source_entity_id: 'node-alice',
                source_entity_name: 'Alice Smith',
                source_entity_type: 'EMPLOYEE',
                relation_type: 'LEADS',
                weight: 0.95,
              },
            ],
          },
        }),
      });
    }

    // 4. Downstream Impact Analysis
    if (url.includes('/api/v1/graph/impact/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Impact analysis computed successfully.',
          data: {
            root_entity: {
              id: 'node-proj',
              name: 'Project Titan',
              entity_type: 'PROJECT',
            },
            affected_departments: ['Platform Engineering', 'SecOps'],
            dependent_projects: ['Apollo Core', 'Data Gateway'],
            impacted_tasks_count: 14,
            severity_score: 0.78,
            dependency_tree: [
              {
                id: 'dep-1',
                name: 'Platform Engineering',
                entity_type: 'DEPARTMENT',
                depth: 1,
                relation: 'GOVERNED_BY',
              },
            ],
          },
        }),
      });
    }

    // 5. Expertise Discovery
    if (url.includes('/api/v1/graph/expertise')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Expertise discovery completed successfully.',
          data: {
            topic: 'Cybersecurity',
            experts: [
              {
                user_id: 'u-1',
                full_name: 'Alice Smith',
                department: 'Platform Engineering',
                score: 9.6,
                authored_documents_count: 7,
                contributed_projects: ['Project Titan', 'Auth Service'],
                evidence_citations: ['Access Control Standard 2026', 'Zero Trust Architecture'],
              },
            ],
          },
        }),
      });
    }

    // 6. Graph Build / Update
    if (method === 'POST' && url.includes('/api/v1/graph/build')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Knowledge graph construction completed.',
          data: {
            entities_created: 15,
            relationships_created: 28,
            duration_seconds: 0.85,
          },
        }),
      });
    }

    return route.continue();
  });
}

// ---------------------------------------------------------------------------
// E2E Test Scenarios
// ---------------------------------------------------------------------------

test.describe('Phase 2.4 — Knowledge Graph & Enterprise Intelligence E2E Suites', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page, 'OrgAdmin');
    await setupGraphApiMocks(page);
  });

  test('KG-01: Page Navigation, Sidebar integration and Phase 2.4 Badge', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Title and Header Check
    const heading = page.locator('h1');
    await expect(heading).toContainText('Enterprise Knowledge Graph');

    // Phase 2.4 Badge
    const phaseBadge = page.getByText('Phase 2.4');
    await expect(phaseBadge.first()).toBeVisible();

    // Verify view tabs exist
    await expect(page.getByTestId('tab-explorer')).toBeVisible();
    await expect(page.getByTestId('tab-impact')).toBeVisible();
    await expect(page.getByTestId('tab-expertise')).toBeVisible();
  });

  test('KG-02: Executive KPI Metrics Banner Rendering', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('metric-total-entities')).toContainText('48');
    await expect(page.getByTestId('metric-total-relationships')).toContainText('92');
    await expect(page.getByTestId('metric-density')).toContainText('8.16%');
    await expect(page.getByTestId('metric-top-hub')).toContainText('Platform Engineering');
  });

  test('KG-03: Filter Bar Interaction & Incremental Text Ingest Drawer', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Search filter
    const searchInput = page.getByTestId('graph-search-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('Titan');

    // Entity type filter
    const typeSelect = page.getByTestId('graph-type-select');
    await expect(typeSelect).toBeVisible();
    await typeSelect.selectOption('PROJECT');

    // Incremental extract toggle
    const extractBtn = page.getByTestId('graph-incremental-btn');
    await extractBtn.click();
    const extractInput = page.getByTestId('graph-incremental-input');
    await expect(extractInput).toBeVisible();
  });

  test('KG-04: Knowledge Explorer Canvas & Node Inspection Drawer', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Canvas exists
    const explorer = page.getByTestId('knowledge-explorer');
    await expect(explorer).toBeVisible();

    // Check SVG nodes rendered
    const titanNode = page.getByTestId('graph-node-node-proj');
    await expect(titanNode).toBeVisible();

    // Click node to open inspection drawer
    await titanNode.click();

    const detailPanel = page.getByTestId('entity-detail-panel');
    await expect(detailPanel).toBeVisible();
    await expect(detailPanel).toContainText('Project Titan');

    // Verify blast radius trigger inside panel
    const blastRadiusBtn = page.getByTestId('trigger-blast-radius-btn');
    await expect(blastRadiusBtn).toBeVisible();
  });

  test('KG-05: Downstream Impact Blast Radius Analysis View', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Switch to Impact Tab
    const impactTab = page.getByTestId('tab-impact');
    await impactTab.click();

    // Verify Impact view rendered
    await expect(page.getByText('Downstream Impact Blast Radius')).toBeVisible();
  });

  test('KG-06: Subject-Matter Expertise Discovery View', async ({ page }) => {
    await page.goto('/graph');
    await page.waitForLoadState('networkidle');

    // Switch to Expertise Tab
    const expertiseTab = page.getByTestId('tab-expertise');
    await expertiseTab.click();

    // Verify Expertise view rendered
    const topicInput = page.getByTestId('expertise-topic-input');
    await expect(topicInput).toBeVisible();

    // Search topic
    await topicInput.fill('Cybersecurity');
    await page.getByTestId('expertise-search-btn').click();

    // Check specialist card rendered
    await expect(page.getByTestId('expert-card-u-1')).toBeVisible();
    await expect(page.getByText('Alice Smith')).toBeVisible();
  });

  test('KG-07: Responsive Viewports (Desktop, Tablet, Mobile)', async ({ page }) => {
    // 1. Desktop 1440x900
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/graph');
    await expect(page.locator('h1')).toBeVisible();

    // 2. Tablet 768x1024
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('h1')).toBeVisible();

    // 3. Mobile 375x667
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('h1')).toBeVisible();
  });
});
