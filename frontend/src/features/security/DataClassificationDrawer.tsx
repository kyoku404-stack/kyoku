/**
 * Phase 3.3 DataClassificationDrawer Component.
 * Interactive deterministic PII scanner and 4-tier data classification engine.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  FileText,
  Shield,
  EyeOff,
  AlertCircle,
  Copy,
  Check,
  Search,
} from 'lucide-react';
import type { DataClassificationScanData } from '@/types/security';
import { ClassificationLevel } from '@/types/security';

interface DataClassificationDrawerProps {
  onClassify: (content: string, documentId?: string) => Promise<DataClassificationScanData | undefined>;
  classificationResult: DataClassificationScanData | null;
  isLoading: boolean;
}

export const DataClassificationDrawer: React.FC<DataClassificationDrawerProps> = ({
  onClassify,
  classificationResult,
  isLoading,
}) => {
  const [inputText, setInputText] = useState('');
  const [copiedPreview, setCopiedPreview] = useState(false);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    await onClassify(inputText);
  };

  const getTierColor = (level?: ClassificationLevel) => {
    switch (level) {
      case ClassificationLevel.RESTRICTED:
        return 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300 border-purple-300 dark:border-purple-800';
      case ClassificationLevel.CONFIDENTIAL:
        return 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border-rose-300 dark:border-rose-800';
      case ClassificationLevel.INTERNAL:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border-blue-300 dark:border-blue-800';
      case ClassificationLevel.PUBLIC:
      default:
        return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700';
    }
  };

  const handleCopyRedacted = () => {
    if (classificationResult?.redacted_preview) {
      navigator.clipboard.writeText(classificationResult.redacted_preview);
      setCopiedPreview(true);
      setTimeout(() => setCopiedPreview(false), 2000);
    }
  };

  return (
    <div className="flex flex-col gap-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-5">
      <div>
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-teal-600 dark:text-teal-400" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            Sensitive Data Classification & PII Scanner
          </h3>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Scans content for PII (SSN, credit cards, emails, phone numbers, API keys, JWTs) and determines zero-trust classification tiers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Scanner Form */}
        <form onSubmit={handleScan} className="flex flex-col gap-3">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Paste Content or Document Text to Inspect
          </label>
          <textarea
            rows={8}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste text containing potential PII or confidential enterprise tokens (e.g., 'Contact admin at john.doe@enterprise.com with secret api_key=ak_live_99482')..."
            className="w-full p-3 text-xs font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 leading-relaxed resize-none"
          />
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-400">
              {inputText.length} characters
            </span>
            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-teal-600 hover:bg-teal-700 text-white transition shadow-sm disabled:opacity-50"
            >
              <Search className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              {isLoading ? 'Scanning Tokens...' : 'Scan & Classify Content'}
            </button>
          </div>
        </form>

        {/* Scan Results Panel */}
        <div className="flex flex-col gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/60">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Scan Results & Inspection Telemetry
            </span>
            {classificationResult && (
              <span
                className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${getTierColor(
                  classificationResult.classification_level
                )}`}
              >
                {classificationResult.classification_level}
              </span>
            )}
          </div>

          {!classificationResult ? (
            <div className="flex flex-col items-center justify-center py-10 text-center text-slate-400">
              <FileText className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-xs">No scan performed yet. Enter content above to evaluate.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {/* Confidence & PII count */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400">PII Entities Found</span>
                  <div className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                    {classificationResult.pii_count}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Confidence Score</span>
                  <div className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                    {(classificationResult.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Detected Entities Chips */}
              <div>
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                  Detected Entity Types:
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {classificationResult.detected_pii_entities.length === 0 ? (
                    <span className="text-xs text-slate-400">None detected (Clean public text)</span>
                  ) : (
                    classificationResult.detected_pii_entities.map((ent, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 text-[11px] font-mono"
                      >
                        <AlertCircle className="w-3 h-3" />
                        {ent.type}: {ent.count} ({ent.masked_sample})
                      </span>
                    ))
                  )}
                </div>
              </div>

              {/* Redacted Preview */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <EyeOff className="w-3.5 h-3.5" />
                    Redacted Preview:
                  </span>
                  <button
                    onClick={handleCopyRedacted}
                    className="text-[11px] text-teal-600 dark:text-teal-400 flex items-center gap-1 hover:underline"
                  >
                    {copiedPreview ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copiedPreview ? 'Copied' : 'Copy Clean Text'}
                  </button>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 text-slate-200 font-mono text-[11px] max-h-36 overflow-y-auto border border-slate-800 whitespace-pre-wrap leading-relaxed">
                  {classificationResult.redacted_preview}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataClassificationDrawer;
