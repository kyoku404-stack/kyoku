/**
 * KEEP Enterprise Platform — Install Plugin Modal & Capability Consent.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import { X, ShieldCheck, Download, AlertCircle } from 'lucide-react';
import type { PluginMarketplaceItem, PluginInstallPayload } from '@/types/plugin';

interface InstallPluginModalProps {
  item: PluginMarketplaceItem | null;
  onClose: () => void;
  onInstall: (payload: PluginInstallPayload) => Promise<unknown>;
}

export const InstallPluginModal: React.FC<InstallPluginModalProps> = ({
  item,
  onClose,
  onInstall,
}) => {
  const [approvedPermissions, setApprovedPermissions] = useState<string[]>(item?.permissions || []);
  const [configJson, setConfigJson] = useState<string>('{\n  \n}');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!item) return null;

  const togglePermission = (perm: string) => {
    setApprovedPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);
      let parsedConfig = {};
      if (configJson.trim()) {
        try {
          parsedConfig = JSON.parse(configJson);
        } catch {
          throw new Error('Configuration must be a valid JSON object');
        }
      }

      await onInstall({
        plugin_id: item.plugin_id,
        version: item.version,
        approved_permissions: approvedPermissions,
        configuration: parsedConfig,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Installation failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 relative shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold">
            {item.name.charAt(0)}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">Install {item.name}</h3>
            <p className="text-xs text-slate-400">Release version {item.version} by {item.developer}</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Permission Consent */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Requested Capabilities & Permissions
            </label>
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 space-y-2 max-h-40 overflow-y-auto">
              {item.permissions.length === 0 ? (
                <p className="text-xs text-slate-500">No special capabilities requested.</p>
              ) : (
                item.permissions.map((perm) => (
                  <label
                    key={perm}
                    className="flex items-center gap-2 text-xs text-slate-300 hover:text-white cursor-pointer select-none"
                  >
                    <input
                      type="checkbox"
                      checked={approvedPermissions.includes(perm)}
                      onChange={() => togglePermission(perm)}
                      className="rounded border-slate-700 text-indigo-600 focus:ring-0 bg-slate-900"
                    />
                    <ShieldCheck className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span>{perm}</span>
                  </label>
                ))
              )}
            </div>
          </div>

          {/* Configuration Initial Values */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Initial Tenant Configuration (JSON)
            </label>
            <textarea
              rows={4}
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              placeholder="e.g. { &quot;api_key&quot;: &quot;sk-123...&quot; }"
              className="w-full bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50"
            />
          </div>

          {/* Action CTAs */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors inline-flex items-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {submitting ? 'Installing...' : 'Confirm & Install'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
