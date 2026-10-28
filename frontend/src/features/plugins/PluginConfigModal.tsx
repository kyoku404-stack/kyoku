/**
 * KEEP Enterprise Platform — Plugin Configuration Editor Modal.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Settings } from 'lucide-react';
import type { PluginItem, PluginConfigUpdatePayload } from '@/types/plugin';

interface PluginConfigModalProps {
  plugin: PluginItem | null;
  onClose: () => void;
  onSaveConfig: (pluginId: string, payload: PluginConfigUpdatePayload) => Promise<unknown>;
}

export const PluginConfigModal: React.FC<PluginConfigModalProps> = ({
  plugin,
  onClose,
  onSaveConfig,
}) => {
  const [configJson, setConfigJson] = useState<string>('{}');
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (plugin) {
      setConfigJson(JSON.stringify(plugin.configuration || {}, null, 2));
    }
  }, [plugin]);

  if (!plugin) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      let parsed = {};
      try {
        parsed = JSON.parse(configJson);
      } catch {
        throw new Error('Configuration must be a valid JSON object');
      }

      await onSaveConfig(plugin.plugin_id, { configuration: parsed });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update configuration');
    } finally {
      setSaving(false);
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
          <div className="p-2.5 rounded-xl bg-slate-800 text-indigo-400 border border-slate-700">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">Configure {plugin.name}</h3>
            <p className="text-xs text-slate-400">Tenant settings for {plugin.plugin_id}</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Configuration Parameters (JSON)
            </label>
            <textarea
              rows={8}
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              className="w-full bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50"
            />
          </div>

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
              disabled={saving}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors inline-flex items-center gap-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
