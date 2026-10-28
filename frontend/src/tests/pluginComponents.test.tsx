/**
 * Phase 3.5 Plugin Feature Components Tests.
 * Author: Member 3 (Frontend & UI Lead)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import {
  PluginMetricsBanner,
  InstalledPluginsList,
  PluginMarketplaceGrid,
  InstallPluginModal,
  PluginConfigModal,
  DeveloperSDKDocumentationModal,
} from '@/features/plugins';
import type {
  PluginAnalytics,
  PluginItem,
  PluginMarketplaceItem,
} from '@/types/plugin';

describe('Phase 3.5 Plugin Feature Components', () => {
  it('PluginMetricsBanner displays all KPIs properly', () => {
    const mockAnalytics: PluginAnalytics = {
      total_installed_plugins: 4,
      active_plugins: 3,
      total_executions: 1250,
      avg_latency_ms: 45.2,
      error_rate: 0.8,
      plugins_by_category: { AI: 2, INTEGRATION: 2 },
    };

    render(<PluginMetricsBanner analytics={mockAnalytics} />);

    expect(screen.getByText('Installed Plugins')).toBeDefined();
    expect(screen.getByText('4')).toBeDefined();
    expect(screen.getByText('3')).toBeDefined();
    expect(screen.getByText('1,250')).toBeDefined();
    expect(screen.getByText('45.2')).toBeDefined();
    expect(screen.getByText('0.8%')).toBeDefined();
  });

  it('InstalledPluginsList renders extensions and triggers callbacks', () => {
    const mockPlugins: PluginItem[] = [
      {
        id: 'inst-1',
        plugin_id: 'sap-s4hana-connector',
        name: 'SAP Enterprise ERP Connector',
        version: '1.2.0',
        category: 'INTEGRATION',
        status: 'ACTIVE',
        is_enabled: true,
        developer: 'SAP SE',
        description: 'Bi-directional ERP sync',
        permissions: ['READ_DOCUMENTS'],
        event_hooks: ['on_document_uploaded'],
        configuration: { host: 'sap.corp' },
      },
    ];

    const onEnable = vi.fn();
    const onDisable = vi.fn();
    const onOpenConfig = vi.fn();
    const onOpenExecute = vi.fn();
    const onUninstall = vi.fn();
    const onRefresh = vi.fn();

    render(
      <InstalledPluginsList
        plugins={mockPlugins}
        loading={false}
        onEnable={onEnable}
        onDisable={onDisable}
        onOpenConfig={onOpenConfig}
        onOpenExecute={onOpenExecute}
        onUninstall={onUninstall}
        onRefresh={onRefresh}
      />
    );

    expect(screen.getByText('SAP Enterprise ERP Connector')).toBeDefined();
    expect(screen.getByText('READ_DOCUMENTS')).toBeDefined();

    // Trigger config button
    const configBtn = screen.getByTitle('Configure Settings');
    fireEvent.click(configBtn);
    expect(onOpenConfig).toHaveBeenCalledWith(mockPlugins[0]);
  });

  it('PluginMarketplaceGrid renders items and handles install click', () => {
    const mockCatalog: PluginMarketplaceItem[] = [
      {
        id: 'tpl-claude',
        plugin_id: 'ai-anthropic-claude',
        name: 'Anthropic Claude Provider',
        description: 'Claude 3.5 Sonnet connector',
        category: 'AI',
        developer: 'Anthropic Partner',
        version: '2.1.0',
        verification_tier: 'CERTIFIED',
        rating: 4.9,
        installs_count: 1420,
        is_installed: false,
        min_keep_version: '3.0.0',
        max_keep_version: '3.9.9',
        permissions: ['AI_INFERENCE'],
        event_hooks: [],
      },
    ];

    const onInstallClick = vi.fn();
    const onOpenPublish = vi.fn();

    render(
      <PluginMarketplaceGrid
        items={mockCatalog}
        loading={false}
        onInstallClick={onInstallClick}
        onOpenPublish={onOpenPublish}
      />
    );

    expect(screen.getByText('Anthropic Claude Provider')).toBeDefined();
    expect(screen.getByText('Certified Enterprise')).toBeDefined();

    const installBtn = screen.getByText('Install Extension');
    fireEvent.click(installBtn);
    expect(onInstallClick).toHaveBeenCalledWith(mockCatalog[0]);
  });

  it('InstallPluginModal submits consent and configuration', async () => {
    const mockItem: PluginMarketplaceItem = {
      id: 'tpl-1',
      plugin_id: 'slack-alerts',
      name: 'Slack Alerts Bot',
      description: 'Sends real-time Slack alerts',
      category: 'WORKFLOW',
      developer: 'Slack',
      version: '1.0.0',
      verification_tier: 'VERIFIED',
      rating: 4.8,
      installs_count: 320,
      is_installed: false,
      min_keep_version: '3.0.0',
      max_keep_version: '3.9.9',
      permissions: ['NETWORK_EGRESS'],
      event_hooks: [],
    };

    const onClose = vi.fn();
    const onInstall = vi.fn().mockResolvedValue({});

    render(
      <InstallPluginModal
        item={mockItem}
        onClose={onClose}
        onInstall={onInstall}
      />
    );

    expect(screen.getByText('Install Slack Alerts Bot')).toBeDefined();
    expect(screen.getByText('NETWORK_EGRESS')).toBeDefined();

    const submitBtn = screen.getByText('Confirm & Install');
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(onInstall).toHaveBeenCalledWith(expect.objectContaining({
      plugin_id: 'slack-alerts',
      version: '1.0.0',
    }));
  });

  it('PluginConfigModal allows editing and saving configuration', async () => {
    const mockPlugin: PluginItem = {
      id: 'inst-1',
      plugin_id: 'ai-claude',
      name: 'Claude AI',
      version: '1.0.0',
      category: 'AI',
      status: 'ACTIVE',
      is_enabled: true,
      permissions: [],
      event_hooks: [],
      configuration: { temperature: 0.5 },
    };

    const onClose = vi.fn();
    const onSave = vi.fn().mockResolvedValue({});

    render(
      <PluginConfigModal
        plugin={mockPlugin}
        onClose={onClose}
        onSaveConfig={onSave}
      />
    );

    expect(screen.getByText('Configure Claude AI')).toBeDefined();
    const saveBtn = screen.getByText('Save Configuration');
    await act(async () => {
      fireEvent.click(saveBtn);
    });
    expect(onSave).toHaveBeenCalledWith('ai-claude', {
      configuration: { temperature: 0.5 },
    });
  });

  it('DeveloperSDKDocumentationModal renders architecture reference and code template', () => {
    const onClose = vi.fn();
    render(<DeveloperSDKDocumentationModal isOpen={true} onClose={onClose} />);

    expect(screen.getByText('Plugin Developer SDK Reference')).toBeDefined();
    expect(screen.getByText('Extension Framework Architecture')).toBeDefined();
  });
});
