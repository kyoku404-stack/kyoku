import React from 'react';
import { DepartmentManager } from '@/features/organization/DepartmentManager';

export const DepartmentsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <DepartmentManager />
    </div>
  );
};

export default DepartmentsPage;
