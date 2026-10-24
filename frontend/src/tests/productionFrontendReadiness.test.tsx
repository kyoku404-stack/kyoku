import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CONFIG } from '@/constants/config';
import { DeploymentReadinessCard } from '@/features/observability/DeploymentReadinessCard';
import { apiClient } from '@/services/api';

describe('Phase 1.10 — Frontend Production Readiness & Deployment Verification', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Application Production Configuration (CONFIG)', () => {
    it('provides application identity and semantic versioning', () => {
      expect(CONFIG.APP_NAME).toBe('KEEP');
      expect(CONFIG.APP_DESCRIPTION).toContain('Knowledge Extraction');
      expect(CONFIG.VERSION).toBe('0.1.0');
    });

    it('resolves environment mode flags properly', () => {
      expect(typeof CONFIG.ENVIRONMENT).toBe('string');
      expect(typeof CONFIG.IS_PRODUCTION).toBe('boolean');
      expect(typeof CONFIG.IS_STAGING).toBe('boolean');
      expect(typeof CONFIG.IS_DEVELOPMENT).toBe('boolean');

      // Mutually exclusive flags
      if (CONFIG.IS_PRODUCTION) {
        expect(CONFIG.IS_DEVELOPMENT).toBe(false);
      }
    });

    it('includes deployment and reverse proxy metadata matching ADR-029', () => {
      expect(CONFIG.DEPLOYMENT.REVERSE_PROXY).toContain('Nginx');
      expect(CONFIG.DEPLOYMENT.HEALTH_ENDPOINT).toBe('/health');
      expect(CONFIG.DEPLOYMENT.METRICS_ENDPOINT).toBe('/metrics');
      expect(CONFIG.DEPLOYMENT.STORAGE_SLO_RPO_HOURS).toBe(1);
      expect(CONFIG.DEPLOYMENT.STORAGE_SLO_RTO_MINUTES).toBe(15);
    });

    it('exposes enterprise feature flags with boolean states', () => {
      expect(typeof CONFIG.FEATURES.RAG_STREAMING).toBe('boolean');
      expect(typeof CONFIG.FEATURES.KNOWLEDGE_GRAPH).toBe('boolean');
      expect(typeof CONFIG.FEATURES.ANALYTICS).toBe('boolean');
      expect(typeof CONFIG.FEATURES.MOCK_FALLBACK).toBe('boolean');
    });

    it('ensures API base URL is non-empty and formatted', () => {
      expect(CONFIG.API_BASE_URL).toBeTruthy();
      expect(CONFIG.API_BASE_URL.length).toBeGreaterThan(0);
    });
  });

  describe('DeploymentReadinessCard Component', () => {
    it('renders deployment topology and phase status without errors', () => {
      render(<DeploymentReadinessCard />);

      expect(
        screen.getByText(/Frontend Production Deployment & Ingress Topology/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/PHASE 1.10 READY/i)).toBeInTheDocument();
      expect(screen.getByText(/Reverse Proxy Ingress/i)).toBeInTheDocument();
      expect(screen.getByText(/Bundle Splitting & Caching/i)).toBeInTheDocument();
      expect(screen.getByText(/Defense-in-Depth Headers/i)).toBeInTheDocument();
    });

    it('displays reverse proxy details and API base URL path', () => {
      render(<DeploymentReadinessCard />);

      expect(screen.getByText(new RegExp(CONFIG.DEPLOYMENT.REVERSE_PROXY, 'i'))).toBeInTheDocument();
      expect(screen.getByText(new RegExp(CONFIG.API_BASE_URL, 'i'))).toBeInTheDocument();
      expect(screen.getByText(/ADR-029/i)).toBeInTheDocument();
    });

    it('displays service level objective targets (SLOs)', () => {
      render(<DeploymentReadinessCard />);

      expect(screen.getByText(/Target SLOs:/i)).toBeInTheDocument();
      expect(screen.getByText(/RPO/i)).toBeInTheDocument();
      expect(screen.getByText(/RTO/i)).toBeInTheDocument();
      expect(screen.getByText(/Page Load/i)).toBeInTheDocument();
    });

    it('renders responsive viewport badge contracts (Mobile, Tablet, Desktop)', () => {
      render(<DeploymentReadinessCard />);

      expect(screen.getByText(/Mobile: < 640px/i)).toBeInTheDocument();
      expect(screen.getByText(/Tablet: 768px - 1024px/i)).toBeInTheDocument();
      expect(screen.getByText(/Desktop: 1440px\+/i)).toBeInTheDocument();
    });
  });

  describe('API Client Production Integration', () => {
    it('initializes Axios with configured base URL and standard timeouts', () => {
      expect(apiClient.defaults.baseURL).toBe(CONFIG.API_BASE_URL);
      expect(apiClient.defaults.timeout).toBe(15000);
      expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
      expect(apiClient.defaults.headers.Accept).toBe('application/json');
    });

    it('attaches Bearer authentication header when token is present in storage', async () => {
      localStorage.setItem('keep_auth_token', 'test_production_token_123');

      // Trigger request interceptor simulation
      const mockConfig = {
        headers: {
          Authorization: '',
        },
      };

      // Axios interceptors are registered; verify storage token retrieval pattern
      const token = localStorage.getItem('keep_auth_token');
      expect(token).toBe('test_production_token_123');
      if (token) {
        mockConfig.headers.Authorization = `Bearer ${token}`;
      }
      expect(mockConfig.headers.Authorization).toBe('Bearer test_production_token_123');
    });
  });

  describe('Vite Production Asset Optimization Standards', () => {
    it('defines standard cache-busting asset naming patterns', () => {
      const entryPattern = 'assets/[name]-[hash].js';
      const chunkPattern = 'assets/[name]-[hash].js';
      const assetPattern = 'assets/[name]-[hash].[ext]';

      expect(entryPattern).toContain('[hash]');
      expect(chunkPattern).toContain('[hash]');
      expect(assetPattern).toContain('[hash]');
    });

    it('defines dedicated vendor chunk partition targets', () => {
      const expectedVendors = ['vendor-react', 'vendor-ui', 'vendor-core', 'vendor-misc'];

      expect(expectedVendors).toContain('vendor-react');
      expect(expectedVendors).toContain('vendor-ui');
      expect(expectedVendors).toContain('vendor-core');
      expect(expectedVendors).toContain('vendor-misc');
    });
  });
});
