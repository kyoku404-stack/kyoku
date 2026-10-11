import React from 'react';
import { TeamManager } from '@/features/organization/TeamManager';

export const TeamsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <TeamManager />
    </div>
  );
};

export default TeamsPage;
