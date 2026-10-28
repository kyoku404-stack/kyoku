/**
 * Phase 3.1 AuthenticateModal Component.
 * Modal for securely providing credentials to activate a connector instance.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  KeyRound,
  ShieldAlert,
  Eye,
  EyeOff,
  CheckCircle,
} from 'lucide-react';
import type {
  ConnectorListItem,
  ConnectorAuthenticateRequest,
  AuthType,
} from '@/types/connector';

interface AuthModalProps {
  isOpen: boolean;
  connector: ConnectorListItem | null;
  onClose: () => void;
  onSubmit: (req: ConnectorAuthenticateRequest) => Promise<boolean>;
}

export const AuthenticateModal: React.FC<AuthModalProps> = ({
  isOpen,
  connector,
  onClose,
  onSubmit,
}) => {
  const [authType, setAuthType] = useState<AuthType>('OAUTH2');
  const [token, setToken] = useState<string>('');
  const [showSecret, setShowSecret] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (!isOpen || !connector) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setFormError('Please enter a valid credential or token.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    const credentials: Record<string, unknown> = {};
    if (authType === 'OAUTH2' || authType === 'OPENID_CONNECT') {
      credentials.access_token = token.trim();
      credentials.expires_in = 3600;
    } else if (authType === 'PERSONAL_ACCESS_TOKEN' || authType === 'API_KEY') {
      credentials.api_key = token.trim();
    } else {
      credentials.service_account_key = token.trim();
    }

    const success = await onSubmit({
      connector_id: connector.id,
      auth_type: authType,
      credentials,
    });

    setIsSubmitting(false);
    if (success) {
      setToken('');
      onClose();
    } else {
      setFormError('Authentication failed. Please verify the credentials.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 sm:p-7">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Authenticate Connector
              </h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {connector.name} ({connector.platform_type})
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {formError && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300">
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Auth Method Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
              Authentication Protocol
            </label>
            <select
              value={authType}
              onChange={(e) => setAuthType(e.target.value as AuthType)}
              className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="OAUTH2">OAuth 2.0 Access Token</option>
              <option value="PERSONAL_ACCESS_TOKEN">Personal Access Token (PAT)</option>
              <option value="API_KEY">API Key / Secret Token</option>
              <option value="SERVICE_ACCOUNT">Service Account Private Key</option>
              <option value="OPENID_CONNECT">OpenID Connect</option>
            </select>
          </div>

          {/* Token/Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Token / Secret Key
              </label>
              <button
                type="button"
                onClick={() => setShowSecret(!showSecret)}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
              >
                {showSecret ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                {showSecret ? 'Hide Secret' : 'Show Secret'}
              </button>
            </div>
            <div className="relative">
              <input
                type={showSecret ? 'text' : 'password'}
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste external platform access token or API key..."
                required
                className="w-full px-3.5 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Security Note */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Credentials will be encrypted with HMAC-SHA256 signature verification. In test mode, entering any string connects the simulated adapter with sample resources.
            </p>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-5 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
            >
              <CheckCircle className="w-4 h-4" />
              {isSubmitting ? 'Authenticating...' : 'Save & Authenticate'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
