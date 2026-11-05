/**
 * KEEP Enterprise Platform — Disaster Recovery & Backup Inventory Panel.
 *
 * Phase: 3.6
 * Role: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  CheckCircle,
  Clock,
  Database,
  FileCheck,
  HardDrive,
  Loader2,
  Plus,
  ShieldCheck,
  X,
} from 'lucide-react';
import type { BackupType, CreateBackupRequest, SystemBackupsData } from '@/types/system';

interface DisasterRecoveryPanelProps {
  backupsData: SystemBackupsData | null;
  onCreateBackup: (request: CreateBackupRequest) => Promise<unknown>;
  creatingBackup: boolean;
}

export const DisasterRecoveryPanel: React.FC<DisasterRecoveryPanelProps> = ({
  backupsData,
  onCreateBackup,
  creatingBackup,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [backupType, setBackupType] = useState<BackupType>('DATABASE');
  const [notes, setNotes] = useState('');

  const rpoTarget = backupsData?.rpo_target_minutes ?? 60;
  const rtoTarget = backupsData?.rto_target_minutes ?? 240;
  const currentDrift = backupsData?.current_rpo_drift_minutes ?? 0;
  const isRpoCompliant = currentDrift <= rpoTarget;
  const backups = backupsData?.backups ?? [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await onCreateBackup({
      backup_type: backupType,
      notes: notes.trim() || undefined,
    });
    setIsModalOpen(false);
    setNotes('');
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '0 MB';
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-md mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            Disaster Recovery & Backup Strategy
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Continuous WAL replication and encrypted snapshots meeting RPO &le; 1h and RTO &le; 4h recovery SLAs.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          Create Snapshot
        </button>
      </div>

      {/* SLA Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 flex items-center gap-3.5">
          <div className={`p-2.5 rounded-lg ${isRpoCompliant ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 block">RPO Target & Drift</span>
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-white">{currentDrift}m drift</span>
              <span className="text-xs text-slate-400">/ {rpoTarget}m target</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 block">RTO Recovery Target</span>
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-white">&le; {rtoTarget / 60} hours</span>
              <span className="text-xs text-emerald-400">Verified</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-400 block">Service Availability</span>
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-white">&ge; 99.9%</span>
              <span className="text-xs text-cyan-400">Target SLA</span>
            </div>
          </div>
        </div>
      </div>

      {/* Backup Inventory Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-700">
            <tr>
              <th className="py-3 px-4 font-medium">Snapshot Name</th>
              <th className="py-3 px-4 font-medium">Type</th>
              <th className="py-3 px-4 font-medium">Status</th>
              <th className="py-3 px-4 font-medium">Archive Size</th>
              <th className="py-3 px-4 font-medium">Integrity SHA-256</th>
              <th className="py-3 px-4 font-medium">Created / Verified</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {backups.map((bak) => (
              <tr key={bak.id} className="hover:bg-slate-800/30 transition-colors">
                <td className="py-3 px-4 font-mono font-medium text-white truncate max-w-xs" title={bak.backup_name}>
                  {bak.backup_name}
                </td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                    {bak.backup_type}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium text-[11px] ${
                    bak.status === 'VERIFIED'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                  }`}>
                    <CheckCircle className="w-3 h-3" />
                    {bak.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-300 font-mono">{formatSize(bak.size_bytes)}</td>
                <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                  {bak.checksum_sha256 ? `${bak.checksum_sha256.slice(0, 12)}...` : 'Pending'}
                </td>
                <td className="py-3 px-4 text-slate-400">
                  {new Date(bak.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Backup Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Create Disaster Recovery Snapshot</h3>
                  <p className="text-xs text-slate-400">Point-in-time encrypted snapshot with SHA-256 seal</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Snapshot Type</label>
                <select
                  value={backupType}
                  onChange={(e) => setBackupType(e.target.value as BackupType)}
                  className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="DATABASE">PostgreSQL Relational DB & pgvector</option>
                  <option value="FULL">Full Platform (Database + Object Storage)</option>
                  <option value="OBJECT_STORAGE">Object Storage S3 Document Assets</option>
                  <option value="WAL">Continuous WAL Archive Segment</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Administrative Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Scheduled pre-maintenance baseline snapshot"
                  rows={3}
                  className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={creatingBackup}
                  className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingBackup}
                  className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-lg shadow-indigo-600/30 transition-all"
                >
                  {creatingBackup ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Initiate Snapshot'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
