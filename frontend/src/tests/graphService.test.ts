/**
 * KEEP Enterprise Platform — Knowledge Graph API Client Unit Tests (Phase 2.4).
 *
 * Verifies all 8 REST endpoints in graphService:
 * - POST /api/v1/graph/build
 * - POST /api/v1/graph/update
 * - GET  /api/v1/graph/entity/:id
 * - GET  /api/v1/graph/relationships/:id
 * - POST /api/v1/graph/query
 * - GET  /api/v1/graph/explorer
 * - GET  /api/v1/graph/expertise
 * - GET  /api/v1/graph/impact/:entity_id
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { graphService } from '@/services/graphService';
import { apiClient } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase 2.4 Knowledge Graph Service API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('buildGraph() sends POST /graph/build with options', async () => {
    const mockData = {
      organization_id: 'org-123',
      entities_created: 15,
      entities_updated: 3,
      relationships_created: 25,
      duration_seconds: 0.85,
      total_entities: 45,
      total_relationships: 80,
    };
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { success: true, message: 'Built successfully', data: mockData },
    });

    const result = await graphService.buildGraph({ rebuild_all: true });

    expect(apiClient.post).toHaveBeenCalledWith('/graph/build', { rebuild_all: true });
    expect(result.success).toBe(true);
    expect(result.data.entities_created).toBe(15);
  });

  it('updateGraph() sends POST /graph/update with text payload', async () => {
    const mockData = {
      entities_extracted: 2,
      relationships_extracted: 1,
      extracted_entities: [{ id: 'e-1', name: 'Alice', entity_type: 'EMPLOYEE' }],
      extracted_relationships: [{ source: 'Alice', relation: 'LEADS', target: 'Project X' }],
    };
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { success: true, message: 'Updated', data: mockData },
    });

    const result = await graphService.updateGraph({ text_content: 'Alice leads Project X' });

    expect(apiClient.post).toHaveBeenCalledWith('/graph/update', { text_content: 'Alice leads Project X' });
    expect(result.data.entities_extracted).toBe(2);
  });

  it('getEntity() sends GET /graph/entity/:id', async () => {
    const mockData = {
      id: 'e-100',
      organization_id: 'org-123',
      name: 'Engineering',
      entity_type: 'DEPARTMENT',
      properties: {},
      in_degree: 5,
      out_degree: 2,
    };
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockData },
    });

    const result = await graphService.getEntity('e-100');

    expect(apiClient.get).toHaveBeenCalledWith('/graph/entity/e-100');
    expect(result.data.name).toBe('Engineering');
    expect(result.data.in_degree).toBe(5);
  });

  it('getEntityRelationships() sends GET /graph/relationships/:id', async () => {
    const mockData = {
      entity_id: 'e-100',
      outgoing_relationships: [
        {
          relationship_id: 'r-1',
          target_entity_id: 'e-200',
          target_entity_name: 'Project Alpha',
          target_entity_type: 'PROJECT',
          relation_type: 'APPLIES_TO',
          weight: 1.0,
        },
      ],
      incoming_relationships: [],
    };
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Retrieved', data: mockData },
    });

    const result = await graphService.getEntityRelationships('e-100');

    expect(apiClient.get).toHaveBeenCalledWith('/graph/relationships/e-100');
    expect(result.data.outgoing_relationships.length).toBe(1);
    expect(result.data.outgoing_relationships[0].relation_type).toBe('APPLIES_TO');
  });

  it('queryGraph() sends POST /graph/query', async () => {
    const mockData = {
      nodes: [{ id: 'e-1', name: 'Start', entity_type: 'PROJECT', depth: 0 }],
      edges: [],
      total_paths: 0,
      max_depth_reached: 0,
    };
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { success: true, message: 'Queried', data: mockData },
    });

    const result = await graphService.queryGraph({ start_entity_id: 'e-1', max_depth: 2 });

    expect(apiClient.post).toHaveBeenCalledWith('/graph/query', { start_entity_id: 'e-1', max_depth: 2 });
    expect(result.data.nodes.length).toBe(1);
  });

  it('getExplorerData() sends GET /graph/explorer with query params', async () => {
    const mockData = {
      nodes: [{ id: 'n-1', label: 'Core Team', type: 'TEAM', val: 15 }],
      links: [],
      metrics: { total_entities: 1, total_relationships: 0, density: 0.0, top_hub: 'Core Team' },
    };
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Loaded', data: mockData },
    });

    const result = await graphService.getExplorerData('TEAM', 50);

    expect(apiClient.get).toHaveBeenCalledWith('/graph/explorer', {
      params: { entity_type: 'TEAM', limit: 50 },
    });
    expect(result.data.metrics.top_hub).toBe('Core Team');
  });

  it('getExpertise() sends GET /graph/expertise with topic', async () => {
    const mockData = {
      topic: 'Cybersecurity',
      experts: [
        {
          user_id: 'u-1',
          full_name: 'Dr. Jane Vance',
          score: 9.2,
          authored_documents_count: 4,
          contributed_projects: ['Security Audit'],
          evidence_citations: ['Security Policy v2'],
        },
      ],
    };
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Found', data: mockData },
    });

    const result = await graphService.getExpertise('Cybersecurity', 5);

    expect(apiClient.get).toHaveBeenCalledWith('/graph/expertise', {
      params: { topic: 'Cybersecurity', limit: 5 },
    });
    expect(result.data.experts[0].score).toBe(9.2);
  });

  it('getImpact() sends GET /graph/impact/:entity_id', async () => {
    const mockData = {
      root_entity: { id: 'pol-1', name: 'Zero Trust Policy', entity_type: 'POLICY' },
      affected_departments: ['Engineering', 'Security'],
      dependent_projects: ['Project Shield'],
      impacted_tasks_count: 12,
      severity_score: 0.85,
      dependency_tree: [],
    };
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { success: true, message: 'Analyzed', data: mockData },
    });

    const result = await graphService.getImpact('pol-1', 4);

    expect(apiClient.get).toHaveBeenCalledWith('/graph/impact/pol-1', {
      params: { max_depth: 4 },
    });
    expect(result.data.severity_score).toBe(0.85);
    expect(result.data.affected_departments).toContain('Engineering');
  });
});
