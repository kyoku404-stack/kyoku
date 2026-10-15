import React, { useState, useRef, useEffect } from 'react';
import {
  Bell,
  Check,
  CheckCheck,
  Info,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import { useNotifications } from '@/hooks/useDashboard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface NotificationCenterProps {
  className?: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
    refresh,
  } = useNotifications(unreadOnly, 10);

  // Close when clicked outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case 'reminder':
        return <Clock className="h-4 w-4 text-sky-500" />;
      case 'security':
        return <ShieldAlert className="h-4 w-4 text-rose-500" />;
      case 'info':
      default:
        return <Info className="h-4 w-4 text-primary" />;
    }
  };

  const formatTimestamp = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Bell Trigger */}
      <Button
        variant="ghost"
        size="icon"
        className="relative text-muted-foreground hover:text-foreground"
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) refresh();
        }}
        aria-label="Notifications"
        aria-expanded={isOpen}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white shadow-sm ring-2 ring-background animate-in zoom-in-50">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </Button>

      {/* Dropdown Popover */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 z-50 w-80 sm:w-96 rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl overflow-hidden animate-in fade-in-50 slide-in-from-top-2">
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-border bg-muted/30">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">Notifications</span>
              {unreadCount > 0 && (
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
                  {unreadCount} unread
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => markAllAsRead()}
                  className="h-7 px-2 text-[11px] text-muted-foreground hover:text-foreground flex items-center gap-1"
                >
                  <CheckCheck className="h-3 w-3" />
                  Mark all read
                </Button>
              )}
            </div>
          </div>

          {/* Filter options */}
          <div className="flex items-center gap-1 px-3 py-1.5 bg-muted/10 border-b border-border/50 text-xs">
            <button
              type="button"
              onClick={() => setUnreadOnly(false)}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                !unreadOnly
                  ? 'bg-primary/10 text-primary font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setUnreadOnly(true)}
              className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                unreadOnly
                  ? 'bg-primary/10 text-primary font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Unread only
            </button>
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-border/40">
            {isLoading && notifications.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground flex flex-col items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                Loading notifications...
              </div>
            ) : notifications.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                No {unreadOnly ? 'unread ' : ''}notifications at this time.
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  className={`p-3 transition-colors hover:bg-muted/50 flex items-start gap-3 ${
                    !item.is_read ? 'bg-primary/5' : ''
                  }`}
                >
                  <div className="mt-0.5 shrink-0">{getCategoryIcon(item.category || item.type)}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className={`text-xs ${!item.is_read ? 'font-semibold text-foreground' : 'text-foreground/90'}`}>
                        {item.title}
                      </p>
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {formatTimestamp(item.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                      {item.message || item.body}
                    </p>
                    {(item.link_url || item.action_url) && (
                      <a
                        href={item.link_url || item.action_url || '#'}
                        className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline mt-1"
                        onClick={() => {
                          if (!item.is_read) markAsRead(item.id);
                          setIsOpen(false);
                        }}
                      >
                        <span>View details</span>
                        <ExternalLink className="h-2.5 w-2.5" />
                      </a>
                    )}
                  </div>
                  {!item.is_read && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 shrink-0 text-muted-foreground hover:text-primary hover:bg-muted"
                      onClick={() => markAsRead(item.id)}
                      title="Mark as read"
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-2 border-t border-border bg-muted/20 text-center">
            <span className="text-[11px] text-muted-foreground">
              KEEP Real-Time Notification Center
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
