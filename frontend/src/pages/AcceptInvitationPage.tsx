import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { AcceptInvitationForm } from '@/features/organization/AcceptInvitationForm';

export const AcceptInvitationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  return (
    <div className="py-12 px-4">
      <AcceptInvitationForm initialToken={token} />
    </div>
  );
};

export default AcceptInvitationPage;
