/**
 * Phase 3.4 WorkflowTemplateGallery Component.
 * Pre-configured blueprint cards for rapid deployment of enterprise automation workflows.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React from 'react';
import {
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import type { WorkflowCreatePayload, WorkflowTemplateItem } from '@/types/workflow';

interface WorkflowTemplateGalleryProps {
  templates: WorkflowTemplateItem[];
  onSelectTemplate: (payload: WorkflowCreatePayload) => void;
}

const complexityColors: Record<string, string> = {
  simple: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
  medium: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300',
  advanced: 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300',
};

export const WorkflowTemplateGallery: React.FC<WorkflowTemplateGalleryProps> = ({
  templates,
  onSelectTemplate,
}) => {
  const handleDeploy = (tpl: WorkflowTemplateItem) => {
    const payload: WorkflowCreatePayload = {
      name: tpl.name,
      description: tpl.description,
      trigger_type: tpl.trigger_type,
      condition_rules: tpl.condition_rules,
      is_active: true,
      steps: tpl.steps_template.map((s, idx) => ({
        step_order: s.step_order || idx + 1,
        name: s.name,
        action_type: s.action_type,
        action_config: s.action_config || {},
      })),
    };
    onSelectTemplate(payload);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-indigo-500" />
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Workflow Template Blueprints
        </h2>
        <span className="text-xs text-slate-400">
          Ready-to-use production automation patterns
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((tpl) => (
          <div
            key={tpl.id}
            className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-850 shadow-xs hover:border-indigo-400 dark:hover:border-indigo-600 transition-all flex flex-col justify-between gap-4"
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  {tpl.category}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    complexityColors[tpl.complexity] || complexityColors.simple
                  }`}
                >
                  {tpl.complexity}
                </span>
              </div>

              <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">
                {tpl.name}
              </h3>

              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                {tpl.description}
              </p>

              <div className="pt-2 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span className="font-medium text-indigo-600 dark:text-indigo-400">
                  Trigger:
                </span>
                <code className="text-[11px] font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                  {tpl.trigger_type}
                </code>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-400 font-mono">
                {tpl.steps_template?.length ?? 0} actions
              </span>
              <button
                type="button"
                onClick={() => handleDeploy(tpl)}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 rounded-lg transition-colors"
              >
                <span>Deploy Template</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
