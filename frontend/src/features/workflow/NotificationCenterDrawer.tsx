/**
 * Phase 3.4 NotificationCenterDrawer Component.
 * Slide-over drawer displaying multi-channel notifications inbox with category filtering and mark-as-read controls.
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useState } from 'react';
import {
  X,
  Bell,
  Check,
  CheckCheck,
  Filter,
  ExternalLink,
  ShieldAlert,
  Zap,
  Info,
  ListTodo,
} from 'lucide-react';
import type { NotificationCategory, NotificationItem, NotificationPriority } from '@/types/workflow';

interface NotificationCenterDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  unreadCount: number;
  onMarkRead: (id: string) => Promise<unknown>;
  onMarkAllRead: () => Promise<unknown>;
}

const priorityBadges: Record<NotificationPriority, { label: string; color: string }> = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' },
  normal: { label: 'Normal', color: 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300' },
  high: { label: 'High', color: 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300' },
  urgent: { label: 'Urgent', color: 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300' },
};

const categoryIcons: Record<NotificationCategory, React.ReactNode> = {
  workflow: <Zap className="w-4 h-4 text-indigo-500" />,
  security: <ShieldAlert className="w-4 h-4 text-rose-500" />,
  system: <Info className="w-4 h-4 text-blue-500" />,
  task: <ListTodo className="w-4 h-4 text-emerald-500" />,
};

export const NotificationCenterDrawer: React.FC<NotificationCenterDrawerProps> = ({
  isOpen,
  onClose,
  notifications,
  unreadCount,
  onMarkRead,
  onMarkAllRead,
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState<boolean>(false);

  if (!isOpen) return null;

  const filteredNotifications = notifications.filter((n) => {
    if (showUnreadOnly && n.is_read) return false;
    if (filterCategory !== 'all' && n.category !== filterCategory) return false;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/50 backdrop-blur-xs">
      <div className="w-full max-w-md bg-white dark:bg-slate-850 h-full shadow-2xl border-l border-slate-200 dark:border-slate-800 flex flex-col">
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Notification Inbox
            </h3>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold bg-rose-500 text-white rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={onMarkAllRead}
                title="Mark all as read"
                className="p-1.5 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/60 rounded-lg flex items-center gap-1 transition-colors"
              >
                <CheckCheck className="w-4 h-4" />
                <span className="hidden sm:inline">Mark all read</span>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="px-5 py-2.5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="text-xs bg-transparent border-0 text-slate-700 dark:text-slate-300 font-medium focus:ring-0 cursor-pointer"
            >
              <option value="all">All Categories</option>
              <option value="workflow">Workflow</option>
              <option value="security">Security</option>
              <option value="system">System</option>
              <option value="task">Tasks</option>
            </select>
          </div>

          <label className="flex items-center gap-1.5 cursor-pointer text-slate-600 dark:text-slate-400">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="w-3.5 h-3.5 text-indigo-600 rounded border-slate-300"
            />
            <span>Unread only</span>
          </label>
        </div>

        {/* Notification List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
          {filteredNotifications.length === 0 ? (
            <div className="py-16 text-center text-slate-500 dark:text-slate-400">
              <Bell className="w-8 h-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
              <p className="text-sm font-medium">Inbox is empty</p>
              <p className="text-xs text-slate-400 mt-1">
                You're caught up! Event alerts will appear here in real-time.
              </p>
            </div>
          ) : (
            filteredNotifications.map((notif) => {
              const priority = priorityBadges[notif.priority] || priorityBadges.normal;
              return (
                <div
                  key={notif.id}
                  className={`p-4 transition-colors flex gap-3 ${
                    notif.is_read
                      ? 'bg-white dark:bg-slate-850 hover:bg-slate-50/50 dark:hover:bg-slate-800/50'
                      : 'bg-indigo-50/30 dark:bg-indigo-950/20 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30'
                  }`}
                >
                  <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
                    {categoryIcons[notif.category] || <Info className="w-4 h-4 text-slate-500" />}
                  </div>

                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <h4
                        className={`text-xs font-semibold ${
                          notif.is_read
                            ? 'text-slate-700 dark:text-slate-300'
                            : 'text-slate-900 dark:text-white'
                        }`}
                      >
                        {notif.title}
                      </h4>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${priority.color}`}>
                        {priority.label}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {notif.content}
                    </p>

                    <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                      <span>{new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>

                      <div className="flex items-center gap-2">
                        {notif.link_url && (
                          <a
                            href={notif.link_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:underline"
                          >
                            <span>Open</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}

                        {!notif.is_read && (
                          <button
                            type="button"
                            onClick={() => onMarkRead(notif.id)}
                            className="inline-flex items-center gap-0.5 text-indigo-600 dark:text-indigo-400 hover:underline"
                          >
                            <Check className="w-3 h-3" />
                            <span>Mark read</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
