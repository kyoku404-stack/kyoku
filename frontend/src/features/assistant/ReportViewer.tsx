import React, { useState } from 'react';
import { FileText, Copy, Download, Check, X, Sparkles } from 'lucide-react';
import type { ReportFormat, ReportGenerateResponseData, ReportType } from '@/types/assistant';

interface ReportViewerProps {
  isOpen: boolean;
  onClose: () => void;
  report: ReportGenerateResponseData | null;
  onGenerateReport: (reportType: ReportType, title: string, format: ReportFormat) => Promise<void>;
  isGenerating?: boolean;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  isOpen,
  onClose,
  report,
  onGenerateReport,
  isGenerating = false,
}) => {
  const [selectedType, setSelectedType] = useState<ReportType>('WEEKLY_ROLLUP');
  const [selectedFormat, setSelectedFormat] = useState<ReportFormat>('MARKDOWN');
  const [customTitle, setCustomTitle] = useState<string>('Engineering Knowledge Base Weekly Rollup');
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (report?.content) {
      navigator.clipboard.writeText(report.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const element = document.createElement('a');
    const file = new Blob([report.content], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = `${report.title.toLowerCase().replace(/\s+/g, '_')}.md`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onGenerateReport(selectedType, customTitle, selectedFormat);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl text-slate-200 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Enterprise Report Generator</h3>
              <p className="text-xs text-slate-400">
                Automated synthesis across organization documentation and analytics
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Generator Controls */}
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4 p-3 bg-slate-950/60 border border-slate-800 rounded-xl">
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Report Type</label>
            <select
              value={selectedType}
              onChange={(e) => {
                const val = e.target.value as ReportType;
                setSelectedType(val);
                setCustomTitle(`${val.replace('_', ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())} Briefing`);
              }}
              className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="WEEKLY_ROLLUP">Weekly Rollup</option>
              <option value="MEETING_SUMMARY">Meeting Summary</option>
              <option value="PROJECT_STATUS">Project Status</option>
              <option value="DEPARTMENT_ANALYTICS">Department Analytics</option>
              <option value="KNOWLEDGE_SYNTHESIS">Knowledge Synthesis</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Report Title</label>
            <input
              type="text"
              value={customTitle}
              onChange={(e) => setCustomTitle(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Format</label>
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value as ReportFormat)}
              className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="MARKDOWN">Markdown</option>
              <option value="JSON">JSON</option>
              <option value="HTML">HTML</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={isGenerating}
              className="w-full py-1.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isGenerating ? 'Synthesizing...' : 'Generate Report'}
            </button>
          </div>
        </form>

        {/* Report Content Preview */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-950/80 border border-slate-800/80 rounded-xl text-slate-300 font-sans text-xs leading-relaxed space-y-3">
          {report ? (
            <pre className="font-mono text-xs whitespace-pre-wrap text-slate-200">
              {report.content}
            </pre>
          ) : (
            <div className="text-center py-12 text-slate-500">
              No report generated yet. Select report parameters above and click &quot;Generate Report&quot;.
            </div>
          )}
        </div>

        {/* Actions Footer */}
        {report && (
          <div className="flex items-center justify-between border-t border-slate-800 pt-4 mt-4">
            <span className="text-xs text-slate-400">
              Export format: <span className="font-semibold text-indigo-400">{report.format}</span>
            </span>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleCopy}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy Markdown'}
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" /> Download (.md)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
