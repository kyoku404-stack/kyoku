/**
 * Phase 3.3 RolePermissionMatrix Component.
 * Interactive enterprise role-based access control (RBAC) permission editor.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState, useEffect } from 'react';
import {
  Users,
  Check,
  Save,
} from 'lucide-react';
import type { RolePermissionItem } from '@/types/security';

interface RolePermissionMatrixProps {
  rolesMatrix: RolePermissionItem[];
  onUpdateRolePermissions: (role: string, permissions: string[]) => Promise<RolePermissionItem | undefined>;
  isLoading: boolean;
}

const ALL_AVAILABLE_PERMISSIONS = [
  'security:view',
  'security:manage',
  'security:audit',
  'security:compliance',
  'data:classify',
  'user:read',
  'user:write',
  'document:read',
  'document:write',
  'document:delete',
  'workspace:create',
  'workspace:manage',
  'chat:read',
  'chat:write',
  'analytics:read',
];

export const RolePermissionMatrix: React.FC<RolePermissionMatrixProps> = ({
  rolesMatrix,
  onUpdateRolePermissions,
  isLoading,
}) => {
  const [selectedRole, setSelectedRole] = useState<string>('SECURITY_OFFICER');
  const [currentPermissions, setCurrentPermissions] = useState<string[]>([]);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    const roleItem = rolesMatrix.find((r) => r.role === selectedRole);
    if (roleItem) {
      setCurrentPermissions(roleItem.permissions);
    } else if (rolesMatrix.length > 0) {
      setSelectedRole(rolesMatrix[0].role);
      setCurrentPermissions(rolesMatrix[0].permissions);
    }
  }, [selectedRole, rolesMatrix]);

  const togglePermission = (perm: string) => {
    setCurrentPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  const handleSave = async () => {
    await onUpdateRolePermissions(selectedRole, currentPermissions);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
  };

  const currentRoleObj = rolesMatrix.find((r) => r.role === selectedRole);

  return (
    <div className="flex flex-col gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Role & Permission Access Matrix
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Fine-grained privilege enforcement across enterprise governance domains
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {saveSuccess && (
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <Check className="w-4 h-4" /> Saved Successfully
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-teal-600 hover:bg-teal-700 text-white transition shadow-sm disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            Save Changes
          </button>
        </div>
      </div>

      {/* Role Selection Tabs */}
      <div className="flex flex-wrap gap-2 pt-1">
        {rolesMatrix.map((item) => (
          <button
            key={item.role}
            onClick={() => setSelectedRole(item.role)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition ${
              selectedRole === item.role
                ? 'bg-teal-50 dark:bg-teal-950/60 border-teal-500 text-teal-700 dark:text-teal-300'
                : 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
            }`}
          >
            {item.role}
          </button>
        ))}
      </div>

      {currentRoleObj && (
        <p className="text-xs text-slate-500 dark:text-slate-400 italic">
          {currentRoleObj.description}
        </p>
      )}

      {/* Permission Checkbox Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-2">
        {ALL_AVAILABLE_PERMISSIONS.map((perm) => {
          const isChecked = currentPermissions.includes(perm);
          const isSecurity = perm.startsWith('security:') || perm.startsWith('data:');
          return (
            <label
              key={perm}
              className={`flex items-center gap-2.5 p-2.5 rounded-lg border cursor-pointer select-none transition ${
                isChecked
                  ? isSecurity
                    ? 'bg-teal-50/50 dark:bg-teal-950/20 border-teal-300 dark:border-teal-800 text-teal-950 dark:text-teal-200'
                    : 'bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-400 hover:border-slate-300'
              }`}
            >
              <input
                type="checkbox"
                checked={isChecked}
                onChange={() => togglePermission(perm)}
                className="w-4 h-4 rounded text-teal-600 focus:ring-teal-500 dark:focus:ring-offset-slate-900"
              />
              <span className="text-xs font-mono font-medium">
                {perm}
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
};

export default RolePermissionMatrix;
