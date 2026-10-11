import React from 'react';
import { OrgSetupWizard } from '@/features/organization/OrgSetupWizard';

export const OrgSetupPage: React.FC = () => {
  return (
    <div className="py-6">
      <OrgSetupWizard onCompleted={() => (window.location.href = '/organization')} />
    </div>
  );
};

export default OrgSetupPage;
