import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useNotifications } from '@/hooks/useDashboard';
import {
  Bell,
  Info,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  ShieldAlert,
  CheckCheck,
  Check,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const NotificationsWidget: React.FC = () => {
  const {
    notifications,
    unreadCount,
    unreadOnly,
    setUnreadOnly,
    isLoading,
    error,
    markAsRead,
    markAllAsRead,
    refresh,
  } = useNotifications(false);

  const getTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case 'reminder':
        return <Calendar className="h-4 w-4 text-blue-500" />;
      case 'security':
        return <ShieldAlert className="h-4 w-4 text-rose-500" />;
      default:
        return <Info className="h-4 w-4 text-indigo-500" />;
    }
  };

  return (
    <Card className="border border-border bg-card flex flex-col h-full shadow-xs">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
              <Bell className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-bold text-foreground">
                  Notifications
                </CardTitle>
                {unreadCount > 0 && (
                  <Badge variant="destructive" className="text-[10px] px-1.5 py-0 h-4">
                    {unreadCount} new
                  </Badge>
                )}
              </div>
              <CardDescription className="text-xs text-muted-foreground">
                Alerts, reminders & system announcements
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={markAllAsRead}
                className="h-7 text-xs gap-1 text-muted-foreground hover:text-foreground"
                title="Mark all notifications as read"
              >
                <CheckCheck className="h-3.5 w-3.5 text-primary" />
                <span className="hidden sm:inline">Mark all read</span>
              </Button>
            )}

            <Button
              variant="ghost"
              size="icon"
              onClick={refresh}
              disabled={isLoading}
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              aria-label="Refresh notifications"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-2 pt-2">
          <button
            onClick={() => setUnreadOnly(false)}
            className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full transition-colors ${
              !unreadOnly
                ? 'bg-primary text-primary-foreground font-semibold'
                : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setUnreadOnly(true)}
            className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full transition-colors ${
              unreadOnly
                ? 'bg-primary text-primary-foreground font-semibold'
                : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            Unread only ({unreadCount})
          </button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-y-auto max-h-[360px]">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-start gap-3 animate-pulse">
                <div className="h-7 w-7 bg-muted rounded-full shrink-0" />
                <div className="space-y-1.5 flex-1">
                  <div className="h-3.5 w-2/3 bg-muted rounded" />
                  <div className="h-3 w-1/2 bg-muted rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : error && notifications.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <p>{error}</p>
            <Button size="sm" variant="outline" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-1">
            <CheckCircle2 className="h-8 w-8 mx-auto text-muted-foreground/30 mb-2" />
            <p className="font-medium text-foreground">You're all caught up!</p>
            <p>No {unreadOnly ? 'unread' : ''} notifications at this time.</p>
          </div>
        ) : (
          <div className="divide-y divide-border/60">
            {notifications.map((n) => (
              <div
                key={n.id}
                className={`p-3.5 flex items-start justify-between gap-3 transition-colors ${
                  !n.is_read ? 'bg-primary/5 hover:bg-primary/10' : 'hover:bg-muted/30'
                }`}
              >
                <div className="flex items-start gap-2.5 min-w-0">
                  <div className="mt-0.5 shrink-0">{getTypeIcon(n.type)}</div>

                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className={`text-xs ${!n.is_read ? 'font-bold text-foreground' : 'font-medium text-muted-foreground'}`}>
                        {n.title}
                      </span>
                      {!n.is_read && (
                        <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                      )}
                    </div>

                    <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
                      {n.body}
                    </p>

                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground pt-0.5">
                      <span>{formatDate(n.created_at)}</span>
                      {n.action_url && (
                        <a
                          href={n.action_url}
                          className="flex items-center gap-0.5 text-primary hover:underline font-medium"
                        >
                          <span>Open</span>
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {!n.is_read && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => markAsRead(n.id)}
                    className="h-6 w-6 text-muted-foreground hover:text-foreground shrink-0 mt-0.5"
                    title="Mark as read"
                  >
                    <Check className="h-3 w-3" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
