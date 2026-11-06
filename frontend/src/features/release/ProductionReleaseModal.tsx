/**
 * KEEP Enterprise Platform — Phase 3.7 Production Release Deployment Modal Component.
 *
 * Form modal for authoring changelogs, validating SemVer tags, and deploying releases.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckSquare,
  Lock,
  Rocket,
  Square,
  Tag,
  X,
} from 'lucide-react';
import type { ReleaseDeployRequest } from '@/types/release';

interface ProductionReleaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeploy: (request: ReleaseDeployRequest) => Promise<unknown>;
  preflightReady: boolean;
  preflightScore: number;
  initialVersion?: string;
  isDeploying?: boolean;
}

export const ProductionReleaseModal: React.FC<ProductionReleaseModalProps> = ({
  isOpen,
  onClose,
  onDeploy,
  preflightReady,
  preflightScore,
  initialVersion = '1.0.0',
  isDeploying = false,
}) => {
  const [version, setVersion] = useState(initialVersion);
  const [releaseTag, setReleaseTag] = useState(`v${initialVersion}`);
  const [environment, setEnvironment] = useState('production');
  const [changelog, setChangelog] = useState(
    '### Release Highlights\n- End-to-end multi-tenant RAG, knowledge graph, and collaboration platform.\n- Automated OWASP Top 10 security audit verified.\n- Zero-downtime production deployment bundle.'
  );
  const [enforcePreflight, setEnforcePreflight] = useState(true);
  const [confirmSafety, setConfirmSafety] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleVersionChange = (val: string) => {
    setVersion(val);
    if (!releaseTag.startsWith('v') || releaseTag === `v${version}`) {
      setReleaseTag(`v${val.replace(/^v/, '')}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // SemVer validation pattern
    const semverRegex = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*)?(?:\+[\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*)?$/;
    const cleanVer = version.replace(/^v/, '').trim();
    if (!semverRegex.test(cleanVer)) {
      setValidationError('Version must conform strictly to SemVer 2.0.0 (e.g. 1.0.0 or 1.0.0-rc.1)');
      return;
    }

    if (!changelog.trim()) {
      setValidationError('Release changelog cannot be empty.');
      return;
    }

    if (!confirmSafety) {
      setValidationError('You must acknowledge the production release safety checklist.');
      return;
    }

    await onDeploy({
      version: cleanVer,
      release_tag: releaseTag.trim() || `v${cleanVer}`,
      changelog: changelog.trim(),
      environment,
      enforce_preflight: enforcePreflight,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-gray-200 dark:border-gray-700 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-700/60 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl">
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                Dispatch Production Release
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                Generate immutable release candidate tag, package container manifests, and deploy.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Close Modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Readiness Warning / Gate Notification */}
        {!preflightReady && (
          <div className="p-4 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700/50 rounded-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 dark:text-amber-200">
              <span className="font-bold">Pre-Flight Gate Warning:</span> Platform readiness score is {Math.round(preflightScore * 100)}% (threshold is 90%). Deploying with pre-flight enforcement enabled will be rejected by backend veto rules.
            </div>
          </div>
        )}

        {validationError && (
          <div className="p-3.5 bg-rose-50 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-700/50 rounded-lg text-xs font-medium text-rose-700 dark:text-rose-300">
            {validationError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Version and Tag Inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                Semantic Version
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={version}
                  onChange={(e) => handleVersionChange(e.target.value)}
                  placeholder="1.0.0"
                  required
                  className="w-full px-3.5 py-2 text-sm bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                Git Release Tag
              </label>
              <div className="relative flex items-center">
                <Tag className="w-4 h-4 text-gray-400 absolute left-3" />
                <input
                  type="text"
                  value={releaseTag}
                  onChange={(e) => setReleaseTag(e.target.value)}
                  placeholder="v1.0.0"
                  required
                  className="w-full pl-9 pr-3.5 py-2 text-sm bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Environment Selector */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
              Target Environment
            </label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-3.5 py-2 text-sm bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
            >
              <option value="production">Production (Default)</option>
              <option value="staging">Staging Pre-Release</option>
              <option value="canary">Canary Cluster</option>
            </select>
          </div>

          {/* Changelog Textarea */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
              Release Notes & Changelog (Markdown)
            </label>
            <textarea
              rows={4}
              value={changelog}
              onChange={(e) => setChangelog(e.target.value)}
              placeholder="Describe features, fixes, and release scope..."
              required
              className="w-full px-3.5 py-2.5 text-xs bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 font-mono resize-y"
            />
          </div>

          {/* Enforcement & Safety Toggles */}
          <div className="space-y-3 pt-2">
            <label className="flex items-center gap-2.5 text-xs text-gray-700 dark:text-gray-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={enforcePreflight}
                onChange={(e) => setEnforcePreflight(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded border-gray-300 dark:border-gray-600 focus:ring-indigo-500"
              />
              <span className="font-medium">
                Enforce Strict Pre-Flight Readiness Gate (Requires ≥ 90% and zero critical failures)
              </span>
            </label>

            <div
              onClick={() => setConfirmSafety(!confirmSafety)}
              className="flex items-start gap-2.5 text-xs text-gray-700 dark:text-gray-300 cursor-pointer select-none p-3 bg-gray-50 dark:bg-gray-900/60 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              {confirmSafety ? (
                <CheckSquare className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              ) : (
                <Square className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
              )}
              <span>
                I acknowledge that this action will freeze version <strong>{version}</strong>, sign the SHA-256 release artifact manifest, and publish the release to the enterprise production cluster.
              </span>
            </div>
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100 dark:border-gray-700/60">
            <button
              type="button"
              onClick={onClose}
              disabled={isDeploying}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isDeploying || !confirmSafety || (enforcePreflight && !preflightReady)}
              className="inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isDeploying ? (
                <>Deploying Release...</>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  Confirm & Deploy Release
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
