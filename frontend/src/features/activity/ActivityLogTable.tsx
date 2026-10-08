import React from 'react';
import type { ActivityLog } from '@/types/activity';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, User, Globe, Clock, Activity } from 'lucide-react';
import { formatDate } from '@/utils/formatters';

interface ActivityLogTableProps {
  logs: ActivityLog[];
  loading?: boolean;
}

const getActionBadge = (action: string) => {
  if (action.includes('LOGIN')) return <Badge variant="success">{action}</Badge>;
  if (action.includes('DELETE')) return <Badge variant="destructive">{action}</Badge>;
  if (action.includes('UPLOAD') || action.includes('CREATE')) return <Badge variant="warning">{action}</Badge>;
  return <Badge variant="secondary">{action}</Badge>;
};

export const ActivityLogTable: React.FC<ActivityLogTableProps> = ({
  logs,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse h-12 bg-muted/40" />
        ))}
      </div>
    );
  }

  if (!logs.length) {
    return (
      <Card className="p-8 text-center text-muted-foreground border-dashed">
        <Activity className="w-12 h-12 mx-auto mb-3 opacity-40 text-primary" />
        <p className="font-medium text-lg text-foreground">No audit logs recorded</p>
        <p className="text-sm mt-1">Enterprise security events, logins, and API actions will record here.</p>
      </Card>
    );
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden bg-card">
      <table className="w-full text-left text-xs">
        <thead className="bg-muted/50 border-b border-border text-muted-foreground font-semibold uppercase">
          <tr>
            <th className="py-2.5 px-4">Action</th>
            <th className="py-2.5 px-4">Resource</th>
            <th className="py-2.5 px-4">Actor</th>
            <th className="py-2.5 px-4">IP Address</th>
            <th className="py-2.5 px-4 text-right">Timestamp</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {logs.map((log) => (
            <tr key={log.id} className="hover:bg-muted/30 transition-colors">
              <td className="py-2.5 px-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-primary" />
                  {getActionBadge(log.action)}
                </div>
              </td>
              <td className="py-2.5 px-4 font-mono text-[11px] text-foreground">
                {log.resource_type} {log.resource_id ? `(${log.resource_id.slice(0, 6)})` : ''}
              </td>
              <td className="py-2.5 px-4 text-muted-foreground">
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {log.user_full_name || log.user_id?.slice(0, 8) || 'System'}
                </span>
              </td>
              <td className="py-2.5 px-4 font-mono text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Globe className="w-3 h-3" />
                  {log.ip_address || '127.0.0.1'}
                </span>
              </td>
              <td className="py-2.5 px-4 text-right text-muted-foreground font-mono text-[11px]">
                <span className="inline-flex items-center gap-1 justify-end">
                  <Clock className="w-3 h-3" />
                  {formatDate(log.created_at)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
