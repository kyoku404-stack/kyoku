import React from 'react';
import { MemberListTable } from '@/features/organization/MemberListTable';

export const MembersPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <MemberListTable />
    </div>
  );
};

export default MembersPage;
