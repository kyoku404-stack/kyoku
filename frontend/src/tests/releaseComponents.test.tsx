/**
 * Phase 3.7 Release Feature Components Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  ProductionReleaseModal,
  ReleaseHistoryTimeline,
  ReleaseReadinessGauge,
  SecurityAuditSummaryCard,
  SponsorDemoLauncher,
} from '@/features/release';
import type {
  ReleaseHistoryItemData,
  SecurityAuditData,
  SystemReadinessData,
} from '@/types/release';

describe('Phase 3.7 Release Feature Components', () => {
  it('ReleaseReadinessGauge renders composite score and checks', () => {
    const mockReadiness: SystemReadinessData = {
      is_ready: true,
      overall_score: 1.0,
      evaluated_at: '2026-11-06T05:00:00Z',
      target_version: '1.0.0',
      git_commit: '8767c08',
      checks: [
        {
          check_name: 'database_migrations',
          category: 'PERSISTENCE',
          status: 'PASSED',
          score: 1.0,
          details: { alembic_head: '1b2c3d4e5f6a' },
          verified_at: '2026-11-06T05:00:00Z',
        },
        {
          check_name: 'vector_database',
          category: 'AI_INFRA',
          status: 'PASSED',
          score: 1.0,
          details: { extension: 'vector' },
          verified_at: '2026-11-06T05:00:00Z',
        },
      ],
      failing_checks: [],
    };

    const handleRefresh = vi.fn();
    const handleOpenModal = vi.fn();

    render(
      <ReleaseReadinessGauge
        readiness={mockReadiness}
        loading={false}
        onRefresh={handleRefresh}
        onOpenReleaseModal={handleOpenModal}
      />
    );

    expect(screen.getByText('Pre-Flight Release Readiness Gate')).toBeDefined();
    expect(screen.getByText('Ready for Deployment')).toBeDefined();
    expect(screen.getByText('100%')).toBeDefined();
    expect(screen.getByText('v1.0.0')).toBeDefined();
    expect(screen.getByText('database migrations')).toBeDefined();
    expect(screen.getByText('vector database')).toBeDefined();

    const deployBtn = screen.getByRole('button', { name: /Deploy Release v1.0.0/i });
    fireEvent.click(deployBtn);
    expect(handleOpenModal).toHaveBeenCalledTimes(1);

    const refreshBtn = screen.getByRole('button', { name: /Refresh Readiness Probe/i });
    fireEvent.click(refreshBtn);
    expect(handleRefresh).toHaveBeenCalledTimes(1);
  });

  it('ProductionReleaseModal renders inputs and handles validation', () => {
    const handleClose = vi.fn();
    const handleDeploy = vi.fn().mockResolvedValue({});

    render(
      <ProductionReleaseModal
        isOpen={true}
        onClose={handleClose}
        onDeploy={handleDeploy}
        preflightReady={true}
        preflightScore={1.0}
        initialVersion="1.0.0"
      />
    );

    expect(screen.getByText('Dispatch Production Release')).toBeDefined();
    expect(screen.getByDisplayValue('1.0.0')).toBeDefined();
    expect(screen.getByDisplayValue('v1.0.0')).toBeDefined();

    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('ReleaseHistoryTimeline renders release items and expandable artifacts', () => {
    const mockReleases: ReleaseHistoryItemData[] = [
      {
        release_id: 'rel-1',
        version: '1.0.0',
        release_tag: 'v1.0.0',
        git_commit: '8767c08',
        status: 'COMPLETED',
        preflight_score: 1.0,
        deployed_by: '00000000-0000-0000-0000-000000000001',
        created_at: '2026-11-06T05:00:00Z',
        completed_at: '2026-11-06T05:00:05Z',
      },
    ];

    render(<ReleaseHistoryTimeline releases={mockReleases} loading={false} />);

    expect(screen.getByText('Release Deployment History')).toBeDefined();
    expect(screen.getByText('v1.0.0')).toBeDefined();
    expect(screen.getByText('Version 1.0.0')).toBeDefined();
    expect(screen.getByText('COMPLETED')).toBeDefined();

    const viewArtifactsBtn = screen.getByRole('button', { name: /View Artifacts/i });
    fireEvent.click(viewArtifactsBtn);
    expect(screen.getByText(/Backend Container Image/i)).toBeDefined();
    expect(screen.getByText(/Frontend SPA Bundle/i)).toBeDefined();
  });

  it('SecurityAuditSummaryCard renders compliance metrics and controls', () => {
    const mockAudit: SecurityAuditData = {
      compliance_standard: 'OWASP_TOP_10_AND_LLM_TOP_10',
      overall_compliance_percent: 100.0,
      evaluated_at: '2026-11-06T05:00:00Z',
      total_controls: 10,
      passed_controls: 10,
      failed_controls: 0,
      controls: [
        {
          control_id: 'SEC-01',
          name: 'SQL Injection Defense',
          status: 'PASSED',
          severity: 'CRITICAL',
          description: 'SQLAlchemy 2.0 ORM parameterization enforced.',
          mitigation: 'Ban raw string queries.',
        },
      ],
      findings: [],
    };

    const handleRefresh = vi.fn();
    render(
      <SecurityAuditSummaryCard
        audit={mockAudit}
        loading={false}
        onRefreshAudit={handleRefresh}
      />
    );

    expect(screen.getByText('Cybersecurity & Compliance Audit')).toBeDefined();
    expect(screen.getByText('Compliant')).toBeDefined();
    expect(screen.getByText('100%')).toBeDefined();
    expect(screen.getByText('SEC-01')).toBeDefined();
    expect(screen.getByText('SQL Injection Defense')).toBeDefined();

    const refreshBtn = screen.getByRole('button', { name: /Re-Run Audit/i });
    fireEvent.click(refreshBtn);
    expect(handleRefresh).toHaveBeenCalledTimes(1);
  });

  it('SponsorDemoLauncher renders 6 enterprise showcase tracks and navigates', () => {
    render(
      <MemoryRouter>
        <SponsorDemoLauncher />
      </MemoryRouter>
    );

    expect(screen.getByText('KEEP Enterprise Platform Architectural Showcase')).toBeDefined();
    expect(screen.getByText('Multi-Tenant RAG & Semantic Search')).toBeDefined();
    expect(screen.getByText('Enterprise AI Assistant & Citations')).toBeDefined();
    expect(screen.getByText('Interactive Knowledge Graph Explorer')).toBeDefined();
    expect(screen.getByText('Real-Time Multi-User Collaboration')).toBeDefined();
    expect(screen.getByText('Sandboxed Plugin & Tool Marketplace')).toBeDefined();
    expect(screen.getByText('Observability & High-Availability Operations')).toBeDefined();
  });
});

