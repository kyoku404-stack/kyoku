/**
 * Phase 3.2 Real-Time Collaboration, Team Workspaces & Knowledge Sharing Master Page.
 * Connects team workspaces, document discussions, live presence, version history, and AI assistance.
 *
 * Specification: devdocs/p3/p3.2.txt & docs/api/api-contract.md Section 14
 * Author: Member 3 (Frontend & UI Lead)
 */

import React, { useEffect, useState } from 'react';
import {
  MessageSquare,
  Clock,
  History,
  Layers,
} from 'lucide-react';
import { useCollaboration } from '@/hooks/useCollaboration';
import {
  WorkspaceHeader,
  WorkspaceGrid,
  CreateWorkspaceModal,
  DocumentDiscussionThread,
  ActivityFeedTimeline,
  VersionHistoryDrawer,
} from '@/features/collaboration';
import { PresenceStatus } from '@/types/collaboration';

export const CollaborationPage: React.FC = () => {
  const {
    workspaces,
    currentWorkspace,
    dashboardData,
    comments,
    presence,
    activities,
    versions,
    aiSummary,
    loading,
    isSummarizing,
    error,
    fetchWorkspaces,
    selectWorkspace,
    createWorkspace,
    fetchComments,
    addComment,
    replyComment,
    resolveComment,
    sendPresence,
    fetchActivities,
    fetchVersions,
    createCheckpoint,
    rollbackVersion,
    summarizeDiscussion,
  } = useCollaboration();

  const [activeTab, setActiveTab] = useState<'workspaces' | 'discussions' | 'activity' | 'versions'>('workspaces');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isVersionDrawerOpen, setIsVersionDrawerOpen] = useState(false);

  // Default active document for collaboration demonstration
  const [selectedDocId] = useState<string>('d1a2b3c4-e5f6-7a8b-9c0d-1e2f3a4b5c6d');
  const [selectedDocTitle] = useState<string>('Employee Handbook.pdf');

  // Load comments & activities when workspace / doc changes
  useEffect(() => {
    if (currentWorkspace) {
      fetchActivities(currentWorkspace.id);
      sendPresence(currentWorkspace.id, PresenceStatus.ONLINE, selectedDocId);
    }
  }, [currentWorkspace, fetchActivities, sendPresence, selectedDocId]);

  useEffect(() => {
    if (selectedDocId) {
      fetchComments(selectedDocId);
      fetchVersions(selectedDocId);
    }
  }, [selectedDocId, fetchComments, fetchVersions]);

  // Periodic heartbeat every 45s
  useEffect(() => {
    if (!currentWorkspace) return;
    const interval = setInterval(() => {
      sendPresence(currentWorkspace.id, PresenceStatus.ONLINE, selectedDocId);
    }, 45000);
    return () => clearInterval(interval);
  }, [currentWorkspace, sendPresence, selectedDocId]);

  return (
    <div className="flex flex-col gap-6 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full animate-in fade-in duration-150">
      {/* Error banner */}
      {error && (
        <div className="p-3.5 rounded-2xl bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-xs border border-red-200/50 flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={() => fetchWorkspaces()}
            className="font-bold underline hover:no-underline ml-2"
          >
            Retry
          </button>
        </div>
      )}

      {/* Header Banner */}
      <WorkspaceHeader
        workspace={currentWorkspace}
        dashboard={dashboardData}
        collaborators={presence}
        onCreateClick={() => setIsCreateModalOpen(true)}
        onRefreshClick={() => {
          fetchWorkspaces();
          if (currentWorkspace) {
            selectWorkspace(currentWorkspace.id);
            fetchActivities(currentWorkspace.id);
          }
          if (selectedDocId) {
            fetchComments(selectedDocId);
          }
        }}
        onToggleActivityFeed={() => setActiveTab('activity')}
        isLoading={loading}
      />

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 pb-1">
        <button
          onClick={() => setActiveTab('workspaces')}
          className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl transition-all ${
            activeTab === 'workspaces'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          Workspaces ({workspaces.length})
        </button>

        <button
          onClick={() => setActiveTab('discussions')}
          className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl transition-all ${
            activeTab === 'discussions'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Document Discussions ({comments.length})
        </button>

        <button
          onClick={() => setActiveTab('activity')}
          className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl transition-all ${
            activeTab === 'activity'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          Activity Feed ({activities.length})
        </button>

        <button
          onClick={() => setIsVersionDrawerOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all ml-auto"
        >
          <History className="w-4 h-4 text-indigo-500" />
          Version Checkpoints ({versions.length})
        </button>
      </div>

      {/* Main Content Area */}
      {activeTab === 'workspaces' && (
        <WorkspaceGrid
          workspaces={workspaces}
          activeWorkspaceId={currentWorkspace?.id}
          onSelectWorkspace={(id) => {
            selectWorkspace(id);
          }}
          onCreateClick={() => setIsCreateModalOpen(true)}
        />
      )}

      {activeTab === 'discussions' && (
        <DocumentDiscussionThread
          documentId={selectedDocId}
          documentTitle={selectedDocTitle}
          workspaceId={currentWorkspace?.id}
          comments={comments}
          aiSummary={aiSummary}
          isSummarizing={isSummarizing}
          onAddComment={addComment}
          onReplyComment={replyComment}
          onResolveComment={resolveComment}
          onSummarizeClick={summarizeDiscussion}
        />
      )}

      {activeTab === 'activity' && currentWorkspace && (
        <ActivityFeedTimeline
          activities={activities}
          workspaceName={currentWorkspace.name}
          onClose={() => setActiveTab('workspaces')}
        />
      )}

      {/* Modals & Slide-Overs */}
      <CreateWorkspaceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={createWorkspace}
      />

      <VersionHistoryDrawer
        isOpen={isVersionDrawerOpen}
        onClose={() => setIsVersionDrawerOpen(false)}
        documentId={selectedDocId}
        documentTitle={selectedDocTitle}
        versions={versions}
        onCreateVersion={createCheckpoint}
        onRollback={rollbackVersion}
      />
    </div>
  );
};
