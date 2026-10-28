/**
 * Phase 3.1 RegisterConnectorModal Component.
 * Interactive modal allowing users to configure and register a new enterprise platform connector.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  HardDrive,
  FileText,
  MessageSquare,
  Code2,
  Kanban,
  Users2,
  ShieldCheck,
} from 'lucide-react';
import type {
  PlatformType,
  PlatformCategory,
  AuthType,
  ConnectorRegisterRequest,
} from '@/types/connector';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (req: ConnectorRegisterRequest) => Promise<boolean>;
}

interface PlatformOption {
  type: PlatformType;
  category: PlatformCategory;
  defaultAuth: AuthType;
  name: string;
  description: string;
}

const PLATFORMS: PlatformOption[] = [
  {
    type: 'GOOGLE_DRIVE',
    category: 'CLOUD_STORAGE',
    defaultAuth: 'OAUTH2',
    name: 'Google Drive',
    description: 'Sync Docs, Sheets, Slides, and enterprise Google Workspace drives.',
  },
  {
    type: 'SHAREPOINT',
    category: 'CLOUD_STORAGE',
    defaultAuth: 'OAUTH2',
    name: 'Microsoft SharePoint',
    description: 'Connect M365 site document libraries, pages, and shared repositories.',
  },
  {
    type: 'ONEDRIVE',
    category: 'CLOUD_STORAGE',
    defaultAuth: 'OAUTH2',
    name: 'Microsoft OneDrive',
    description: 'Ingest enterprise user drives and organizational folders.',
  },
  {
    type: 'GITHUB',
    category: 'DEVELOPMENT',
    defaultAuth: 'PERSONAL_ACCESS_TOKEN',
    name: 'GitHub',
    description: 'Synchronize markdown docs, READMEs, PR notes, and issue discussions.',
  },
  {
    type: 'SLACK',
    category: 'COMMUNICATION',
    defaultAuth: 'OAUTH2',
    name: 'Slack',
    description: 'Index public/private team channels, canvas boards, and discussion threads.',
  },
  {
    type: 'NOTION',
    category: 'DOCUMENTATION',
    defaultAuth: 'PERSONAL_ACCESS_TOKEN',
    name: 'Notion',
    description: 'Import workspaces, databases, pages, and structured team wikis.',
  },
  {
    type: 'JIRA',
    category: 'PROJECT_MANAGEMENT',
    defaultAuth: 'API_KEY',
    name: 'Jira Software',
    description: 'Sync project epics, task backlogs, sprint boards, and tickets.',
  },
  {
    type: 'CONFLUENCE',
    category: 'DOCUMENTATION',
    defaultAuth: 'OAUTH2',
    name: 'Confluence',
    description: 'Ingest departmental spaces, knowledge bases, and architectural guidelines.',
  },
];

export const RegisterConnectorModal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformOption>(PLATFORMS[0]);
  const [name, setName] = useState<string>('');
  const [syncInterval, setSyncInterval] = useState<number>(60);
  const [folders, setFolders] = useState<string>('root, docs');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim() || `${selectedPlatform.name} Connector`;

    setIsSubmitting(true);
    setFormError(null);

    const folderList = folders
      .split(',')
      .map((f) => f.trim())
      .filter((f) => f.length > 0);

    const success = await onSubmit({
      name: trimmedName,
      platform_type: selectedPlatform.type,
      platform_category: selectedPlatform.category,
      auth_type: selectedPlatform.defaultAuth,
      config: {
        sync_interval_minutes: syncInterval,
        sync_folders: folderList.length > 0 ? folderList : ['root'],
        file_extensions: ['.pdf', '.docx', '.md', '.txt'],
      },
    });

    setIsSubmitting(false);
    if (success) {
      setName('');
      onClose();
    } else {
      setFormError('Failed to register connector. Please try again.');
    }
  };

  const getIcon = (category: PlatformCategory) => {
    switch (category) {
      case 'CLOUD_STORAGE':
        return <HardDrive className="w-5 h-5 text-sky-500" />;
      case 'DEVELOPMENT':
        return <Code2 className="w-5 h-5 text-purple-500" />;
      case 'COMMUNICATION':
        return <MessageSquare className="w-5 h-5 text-emerald-500" />;
      case 'DOCUMENTATION':
        return <FileText className="w-5 h-5 text-indigo-500" />;
      case 'PROJECT_MANAGEMENT':
        return <Kanban className="w-5 h-5 text-blue-500" />;
      case 'CRM':
        return <Users2 className="w-5 h-5 text-amber-500" />;
      default:
        return <HardDrive className="w-5 h-5 text-slate-500" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 sm:p-7">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Connect External Platform
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Select an enterprise SaaS repository to integrate into KEEP RAG search.
            </p>
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

        <form onSubmit={handleSubmit} className="mt-5 space-y-5">
          {/* Platform selection grid */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
              Select Platform
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {PLATFORMS.map((p) => {
                const isSelected = selectedPlatform.type === p.type;
                return (
                  <button
                    key={p.type}
                    type="button"
                    onClick={() => {
                      setSelectedPlatform(p);
                      if (!name) setName(`${p.name} Connector`);
                    }}
                    className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                      isSelected
                        ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50/70 dark:bg-indigo-950/60 ring-2 ring-indigo-500/20'
                        : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="mb-1.5">{getIcon(p.category)}</div>
                    <span className="text-xs font-semibold text-slate-900 dark:text-white line-clamp-1">
                      {p.name}
                    </span>
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              {selectedPlatform.description}
            </p>
          </div>

          {/* Connector Name */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
              Connector Display Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={`e.g. Corporate ${selectedPlatform.name}`}
              required
              className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Configuration options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
                Sync Interval (Minutes)
              </label>
              <select
                value={syncInterval}
                onChange={(e) => setSyncInterval(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value={15}>Every 15 minutes</option>
                <option value={30}>Every 30 minutes</option>
                <option value={60}>Every 1 hour (Default)</option>
                <option value={360}>Every 6 hours</option>
                <option value={1440}>Once a day</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1">
                Target Folders / Spaces
              </label>
              <input
                type="text"
                value={folders}
                onChange={(e) => setFolders(e.target.value)}
                placeholder="root, Engineering, Docs"
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Security guarantee note */}
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span className="text-xs text-slate-600 dark:text-slate-300">
              Credentials are encrypted at rest using AES-128/HMAC-SHA256 authenticated encryption. Source platform permissions and RBAC tags will be mapped automatically.
            </span>
          </div>

          {/* Action buttons */}
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
              {isSubmitting ? 'Registering...' : 'Register Connector'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
