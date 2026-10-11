import React from 'react';
import { ProjectWorkspaceView } from '@/features/organization/ProjectWorkspaceView';

export const ProjectsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <ProjectWorkspaceView />
    </div>
  );
};

export default ProjectsPage;
