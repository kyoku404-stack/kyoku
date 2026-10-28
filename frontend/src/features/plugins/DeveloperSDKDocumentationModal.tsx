/**
 * KEEP Enterprise Platform — Developer SDK Documentation Modal.
 *
 * Phase: 3.5
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import { X, Code2, BookOpen, Copy, Check, ShieldCheck, Terminal, Layers } from 'lucide-react';

interface DeveloperSDKDocumentationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeveloperSDKDocumentationModal: React.FC<DeveloperSDKDocumentationModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [copied, setCopied] = useState<string | null>(null);

  if (!isOpen) return null;

  const samplePythonCode = `from backend.app.services.plugins.contracts import (
    BasePlugin,
    PluginCategory,
    PluginCapability,
    PluginExecutionInput,
    PluginExecutionOutput,
    PluginLogStatus,
    PluginManifest,
)

class MyEnterprisePlugin(BasePlugin):
    """Custom enterprise integration extension."""

    def __init__(self) -> None:
        manifest = PluginManifest(
            id="my-custom-plugin",
            name="My Custom Integration",
            version="1.0.0",
            developer="Internal Platform Team",
            description="Automates ledger sync and security event hooks.",
            category=PluginCategory.INTEGRATION,
            entry_point="my_plugin.module:MyEnterprisePlugin",
            min_keep_version="3.0.0",
            max_keep_version="3.9.9",
            permissions=[PluginCapability.DOCUMENTS_READ.value, PluginCapability.NETWORK_OUTBOUND.value],
            event_hooks=["on_document_uploaded"],
        )
        super().__init__(manifest)

    def initialize(self, config: dict) -> None:
        self.api_endpoint = config.get("api_endpoint")

    async def execute(self, execution_input: PluginExecutionInput) -> dict:
        # Perform sandboxed workload
        return {
            "status": "PROCESSED",
            "action": execution_input.action,
            "items_count": len(execution_input.parameters),
        }

    async def on_event(self, event_topic: str, payload: dict) -> dict:
        # Event hook listener
        return {"handled_event": event_topic, "status": "ACK"}
`;

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl relative">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight">Plugin Developer SDK Reference</h3>
              <p className="text-xs text-slate-400">Author, sandbox, and register enterprise KEEP extensions</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-slate-300">
          {/* Quick Overview */}
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
            <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-400" /> Extension Framework Architecture
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              KEEP plugins run inside an isolated asynchronous runtime sandbox. Every extension specifies
              strict SemVer compatibility constraints, requests explicit platform capabilities (e.g.{' '}
              <code className="text-indigo-300 font-mono">Documents.Read</code>,{' '}
              <code className="text-indigo-300 font-mono">Network.Outbound</code>), and subscribes to asynchronous event
              topics without blocking core API threads.
            </p>
          </div>

          {/* Plugin Code Example */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" /> Python BasePlugin Implementation
              </span>
              <button
                onClick={() => copyToClipboard(samplePythonCode, 'code')}
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
              >
                {copied === 'code' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied === 'code' ? 'Copied' : 'Copy Template'}
              </button>
            </div>
            <pre className="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-300 overflow-x-auto leading-relaxed">
              {samplePythonCode}
            </pre>
          </div>

          {/* Capabilities & Security */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
              <h5 className="font-semibold text-white text-xs mb-2 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" /> Capability Permissions
              </h5>
              <ul className="text-xs space-y-1 text-slate-400">
                <li>• <strong className="text-slate-300 font-mono">AI_INFERENCE</strong>: LLM invocation & prompt pipelines</li>
                <li>• <strong className="text-slate-300 font-mono">READ_DOCUMENTS</strong>: Read enterprise knowledge base</li>
                <li>• <strong className="text-slate-300 font-mono">NETWORK_EGRESS</strong>: Outbound REST & webhook calls</li>
                <li>• <strong className="text-slate-300 font-mono">EVENT_LISTEN</strong>: Subscribe to audit and lifecycle hooks</li>
              </ul>
            </div>

            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
              <h5 className="font-semibold text-white text-xs mb-2 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-purple-400" /> Extension Categories
              </h5>
              <ul className="text-xs space-y-1 text-slate-400">
                <li>• <strong className="text-slate-300">AI</strong>: Third-party LLM & multimodal providers</li>
                <li>• <strong className="text-slate-300">INTEGRATION</strong>: ERP, CRM, and SaaS connectors</li>
                <li>• <strong className="text-slate-300">WORKFLOW</strong>: Approval bots and event triggers</li>
                <li>• <strong className="text-slate-300">ANALYTICS</strong>: Custom BI metrics & reporting exporters</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors"
          >
            Close Documentation
          </button>
        </div>
      </div>
    </div>
  );
};
