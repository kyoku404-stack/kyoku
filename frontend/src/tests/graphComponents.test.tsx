/**
 * KEEP Enterprise Platform — Knowledge Graph UI Components Unit & Integration Tests (Phase 2.4).
 *
 * Verifies rendering, interactions, filtering, inspection, and view switching for:
 * - GraphMetricsBanner
 * - GraphFilterBar
 * - KnowledgeExplorer
 * - EntityDetailPanel
 * - ImpactAnalysisWidget
 * - ExpertiseDirectory
 * - KnowledgeGraphPage
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

import {
  GraphMetricsBanner,
  GraphFilterBar,
  KnowledgeExplorer,
  EntityDetailPanel,
  ImpactAnalysisWidget,
  ExpertiseDirectory,
} from '@/features/graph';
import { KnowledgeGraphPage } from '@/pages/KnowledgeGraphPage';
import { graphService } from '@/services/graphService';

vi.mock('@/services/graphService', () => ({
  graphService: {
    getExplorerData: vi.fn(),
    getEntity: vi.fn(),
    getEntityRelationships: vi.fn(),
    buildGraph: vi.fn(),
    updateGraph: vi.fn(),
    queryGraph: vi.fn(),
    getExpertise: vi.fn(),
    getImpact: vi.fn(),
  },
}));

describe('Phase 2.4 Knowledge Graph UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('GraphMetricsBanner', () => {
    it('renders topology metrics and top hub card', () => {
      const mockMetrics = {
        total_entities: 120,
        total_relationships: 260,
        density: 0.045,
        top_hub: 'Engineering Department',
      };

      render(<GraphMetricsBanner metrics={mockMetrics} />);

      expect(screen.getByTestId('metric-total-entities')).toHaveTextContent('120');
      expect(screen.getByTestId('metric-total-relationships')).toHaveTextContent('260');
      expect(screen.getByTestId('metric-density')).toHaveTextContent('4.50%');
      expect(screen.getByTestId('metric-top-hub')).toHaveTextContent('Engineering Department');
    });

    it('handles empty/loading state gracefully', () => {
      render(<GraphMetricsBanner metrics={null} loading={true} />);
      expect(screen.getByTestId('metric-total-entities')).toHaveTextContent('—');
    });
  });

  describe('GraphFilterBar', () => {
    it('triggers search and filter callbacks', () => {
      const onFilterChange = vi.fn();
      const onRefresh = vi.fn();
      const onTriggerBuild = vi.fn();
      const onTriggerUpdate = vi.fn();

      const initialFilters = {
        searchQuery: '',
        selectedEntityType: 'ALL',
        maxDepth: 2,
        showOrphans: true,
      };

      render(
        <GraphFilterBar
          filters={initialFilters}
          onFilterChange={onFilterChange}
          onRefresh={onRefresh}
          onTriggerBuild={onTriggerBuild}
          onTriggerUpdate={onTriggerUpdate}
        />
      );

      const searchInput = screen.getByTestId('graph-search-input');
      fireEvent.change(searchInput, { target: { value: 'Quantum' } });
      expect(onFilterChange).toHaveBeenCalledWith(
        expect.objectContaining({ searchQuery: 'Quantum' })
      );

      const refreshBtn = screen.getByTestId('graph-refresh-btn');
      fireEvent.click(refreshBtn);
      expect(onRefresh).toHaveBeenCalled();

      const buildBtn = screen.getByTestId('graph-build-btn');
      fireEvent.click(buildBtn);
      expect(onTriggerBuild).toHaveBeenCalledWith(false);
    });
  });

  describe('KnowledgeExplorer', () => {
    it('renders SVG nodes, links, and triggers onSelectEntity', () => {
      const mockNodes = [
        { id: 'node-1', label: 'AI Migration', type: 'PROJECT', val: 20 },
        { id: 'node-2', label: 'Alice Smith', type: 'EMPLOYEE', val: 15 },
      ];
      const mockLinks = [
        { source: 'node-2', target: 'node-1', label: 'LEADS', weight: 0.95 },
      ];
      const onSelect = vi.fn();

      render(
        <KnowledgeExplorer
          nodes={mockNodes}
          links={mockLinks}
          selectedEntityId={null}
          onSelectEntity={onSelect}
        />
      );

      expect(screen.getByTestId('knowledge-explorer')).toBeInTheDocument();
      expect(screen.getByText('AI Migration')).toBeInTheDocument();
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();

      const node1 = screen.getByTestId('graph-node-node-1');
      fireEvent.click(node1);
      expect(onSelect).toHaveBeenCalledWith('node-1');
    });
  });

  describe('EntityDetailPanel', () => {
    it('displays entity metadata and relationship connections', () => {
      const mockEntity = {
        id: 'node-1',
        organization_id: 'org-1',
        name: 'AI Migration Project',
        entity_type: 'PROJECT',
        properties: { status: 'ACTIVE' },
        in_degree: 2,
        out_degree: 3,
      };
      const mockRels = {
        entity_id: 'node-1',
        outgoing_relationships: [
          {
            relationship_id: 'r-out-1',
            target_entity_id: 'node-dept',
            target_entity_name: 'Engineering',
            target_entity_type: 'DEPARTMENT',
            relation_type: 'APPLIES_TO',
            weight: 1.0,
          },
        ],
        incoming_relationships: [],
      };
      const onClose = vi.fn();
      const onAnalyzeImpact = vi.fn();
      const onSelectConnected = vi.fn();

      render(
        <EntityDetailPanel
          entity={mockEntity}
          relationships={mockRels}
          onClose={onClose}
          onAnalyzeImpact={onAnalyzeImpact}
          onSelectConnectedEntity={onSelectConnected}
        />
      );

      expect(screen.getByTestId('entity-detail-panel')).toBeInTheDocument();
      expect(screen.getByText('AI Migration Project')).toBeInTheDocument();
      expect(screen.getByText('Engineering')).toBeInTheDocument();

      const impactBtn = screen.getByTestId('btn-analyze-impact');
      fireEvent.click(impactBtn);
      expect(onAnalyzeImpact).toHaveBeenCalledWith('node-1');

      const closeBtn = screen.getByTestId('close-detail-panel');
      fireEvent.click(closeBtn);
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('ImpactAnalysisWidget', () => {
    it('renders severity score and affected scope', () => {
      const mockImpact = {
        root_entity: { id: 'e-root', name: 'Access Control Standard', entity_type: 'POLICY' },
        affected_departments: ['Engineering', 'Security'],
        dependent_projects: ['Project Titan'],
        impacted_tasks_count: 5,
        severity_score: 0.75,
        dependency_tree: [
          { id: 'dep-1', name: 'Project Titan', entity_type: 'PROJECT', depth: 1, relation: 'GOVERNED_BY' },
        ],
      };
      const onClose = vi.fn();

      render(<ImpactAnalysisWidget impact={mockImpact} onClose={onClose} />);

      expect(screen.getByTestId('impact-analysis-widget')).toBeInTheDocument();
      expect(screen.getByText(/Access Control Standard/)).toBeInTheDocument();
      expect(screen.getByText('High Risk (75%)')).toBeInTheDocument();
      expect(screen.getAllByText('Project Titan').length).toBeGreaterThan(0);
    });
  });

  describe('ExpertiseDirectory', () => {
    it('allows searching topic and rendering ranked specialists', () => {
      const mockExpertise = {
        topic: 'Cybersecurity',
        experts: [
          {
            user_id: 'u-1',
            full_name: 'Alice Smith',
            department: 'Engineering',
            score: 9.5,
            authored_documents_count: 5,
            contributed_projects: ['Security Audit'],
            evidence_citations: ['Security Standard 2026'],
          },
        ],
      };
      const onSearch = vi.fn();

      render(<ExpertiseDirectory expertise={mockExpertise} onSearchTopic={onSearch} />);

      expect(screen.getByTestId('expertise-directory')).toBeInTheDocument();
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
      expect(screen.getByText('9.5 / 10')).toBeInTheDocument();
      expect(screen.getByText(/5 docs authored/)).toBeInTheDocument();
    });
  });

  describe('KnowledgeGraphPage Integration', () => {
    it('loads page, renders banner, filter bar, and switches view tabs', async () => {
      vi.mocked(graphService.getExplorerData).mockResolvedValue({
        success: true,
        message: 'Loaded',
        data: {
          nodes: [{ id: 'n-1', label: 'Test Node', type: 'PROJECT', val: 15 }],
          links: [],
          metrics: { total_entities: 1, total_relationships: 0, density: 0.0, top_hub: 'Test Node' },
        },
      });

      render(
        <BrowserRouter>
          <KnowledgeGraphPage />
        </BrowserRouter>
      );

      expect(screen.getByTestId('knowledge-graph-page')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Graph & Enterprise Intelligence')).toBeInTheDocument();

      await waitFor(() => {
        expect(graphService.getExplorerData).toHaveBeenCalled();
      });

      // Tab switching
      const impactTab = screen.getByTestId('tab-impact');
      fireEvent.click(impactTab);
      expect(screen.getByText(/Select an entity from the Topology Explorer/)).toBeInTheDocument();

      const expertiseTab = screen.getByTestId('tab-expertise');
      fireEvent.click(expertiseTab);
      expect(screen.getByTestId('expertise-directory')).toBeInTheDocument();
    });
  });
});
