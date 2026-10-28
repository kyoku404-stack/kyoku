/**
 * Phase 3.3 MFASetupModal Component.
 * Implements RFC 6238 TOTP Multi-Factor Authentication enrollment, verification,
 * backup codes generation/download, and disable flows.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  ShieldCheck,
  KeyRound,
  Copy,
  Check,
  Download,
  AlertTriangle,
  QrCode,
} from 'lucide-react';
import type { MFASetupData } from '@/types/security';

interface MFASetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  mfaSetup: MFASetupData | null;
  mfaEnabled: boolean;
  onSetupMFA: () => Promise<MFASetupData | undefined>;
  onVerifyMFA: (code: string) => Promise<unknown>;
  onDisableMFA: (code: string) => Promise<unknown>;
  isLoading: boolean;
}

export const MFASetupModal: React.FC<MFASetupModalProps> = ({
  isOpen,
  onClose,
  mfaSetup,
  mfaEnabled,
  onSetupMFA,
  onVerifyMFA,
  onDisableMFA,
  isLoading,
}) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isDisabling, setIsDisabling] = useState(false);

  if (!isOpen) return null;

  const handleCopyKey = () => {
    if (mfaSetup?.secret_key) {
      navigator.clipboard.writeText(mfaSetup.secret_key);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const handleCopyBackupCodes = () => {
    if (mfaSetup?.backup_codes) {
      navigator.clipboard.writeText(mfaSetup.backup_codes.join('\n'));
      setCopiedCodes(true);
      setTimeout(() => setCopiedCodes(false), 2000);
    }
  };

  const handleDownloadBackupCodes = () => {
    if (mfaSetup?.backup_codes) {
      const blob = new Blob([mfaSetup.backup_codes.join('\n')], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mfa-backup-codes-${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode || verificationCode.length !== 6) {
      setErrorMsg('Please enter a valid 6-digit TOTP code');
      return;
    }
    setErrorMsg(null);
    try {
      if (isDisabling) {
        await onDisableMFA(verificationCode);
        setSuccessMsg('Multi-Factor Authentication disabled successfully.');
      } else {
        await onVerifyMFA(verificationCode);
        setSuccessMsg('Multi-Factor Authentication enabled and verified!');
      }
      setVerificationCode('');
      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Action failed. Check your 6-digit code.';
      setErrorMsg(msg);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 flex items-center justify-center">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                {mfaEnabled ? 'Manage Multi-Factor Authentication' : 'Setup Multi-Factor Authentication'}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                RFC 6238 Standard Time-Based One-Time Password (TOTP)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 flex flex-col gap-4 max-h-[75vh] overflow-y-auto">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {mfaEnabled && !mfaSetup ? (
            <div className="flex flex-col gap-4">
              <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div className="text-xs text-emerald-900 dark:text-emerald-200">
                  <p className="font-semibold text-sm">MFA is Active & Enforced</p>
                  <p className="mt-1 text-emerald-800 dark:text-emerald-300">
                    Your account is protected with TOTP authentication. You will be prompted for your 6-digit code during future logins.
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                  To disable MFA or re-configure your authenticator app, verify your current 6-digit TOTP code below.
                </p>
                <form onSubmit={handleVerify} className="flex flex-col gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Current 6-Digit Authenticator Code
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                      className="w-full px-3 py-2 text-center text-lg tracking-widest font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <button
                    type="submit"
                    onClick={() => setIsDisabling(true)}
                    disabled={isLoading || verificationCode.length !== 6}
                    className="w-full py-2 px-4 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs transition disabled:opacity-50"
                  >
                    Disable Multi-Factor Authentication
                  </button>
                </form>
              </div>
            </div>
          ) : !mfaSetup ? (
            <div className="flex flex-col items-center justify-center py-6 text-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <QrCode className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Protect Your Enterprise Identity
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mt-1">
                  Enforce hardware or software-based time authenticator apps (Google Authenticator, Microsoft Authenticator, 1Password, or YubiKey).
                </p>
              </div>
              <button
                type="button"
                onClick={() => onSetupMFA()}
                disabled={isLoading}
                className="mt-2 px-4 py-2 text-xs font-semibold rounded-lg bg-teal-600 hover:bg-teal-700 text-white transition shadow-sm"
              >
                Start MFA Enrollment
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {/* Step 1: Secret Key & URI */}
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Step 1: Enter Secret Key in Authenticator
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={mfaSetup.secret_key}
                    className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200 select-all"
                  />
                  <button
                    type="button"
                    onClick={handleCopyKey}
                    className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 text-xs flex items-center gap-1.5 transition"
                  >
                    {copiedKey ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedKey ? 'Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              {/* Step 2: Verification Code Input */}
              <form onSubmit={handleVerify} className="flex flex-col gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Step 2: Enter 6-Digit Authenticator Code
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                    className="w-full px-3 py-2 text-center text-xl tracking-widest font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading || verificationCode.length !== 6}
                  className="w-full py-2.5 px-4 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs transition disabled:opacity-50 shadow-sm"
                >
                  Verify & Activate MFA
                </button>
              </form>

              {/* Step 3: Backup Codes */}
              {mfaSetup.backup_codes && mfaSetup.backup_codes.length > 0 && (
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Emergency Backup Codes
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={handleCopyBackupCodes}
                        className="p-1 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-xs"
                        title="Copy All"
                      >
                        {copiedCodes ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                      <button
                        type="button"
                        onClick={handleDownloadBackupCodes}
                        className="p-1 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-xs"
                        title="Download .txt"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                    {mfaSetup.backup_codes.map((code, idx) => (
                      <span key={idx} className="bg-white dark:bg-slate-900 px-2 py-1 rounded border border-slate-200 dark:border-slate-800 text-center">
                        {code}
                      </span>
                    ))}
                  </div>
                  <p className="text-[10px] text-amber-600 dark:text-amber-400">
                    Save these codes in a safe place. Each code can be used once if you lose device access.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MFASetupModal;
