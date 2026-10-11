import React from 'react';
import { OrgSettingsView } from '@/features/organization/OrgSettingsView';

export const OrgSettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <OrgSettingsView />
    </div>
  );
};

export default OrgSettingsPage;
