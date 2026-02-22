import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '@/presentation/ui/button';
import { Badge } from '@/presentation/ui/badge';
import { Card, CardContent } from '@/presentation/ui/card';
import { ScrollArea } from '@/presentation/ui/scroll-area';
import { Skeleton } from '@/presentation/ui/skeleton';
import { getMyActivityLogs } from '@/infrastructure/api/activity.api';
import type { AuditLogEntry } from '@/domain/activity/types';

const PAGE_SIZE = 50;

function getActionColor(action: string): string {
  const lower = action.toLowerCase();
  if (lower.includes('upload') || lower.includes('create')) return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400';
  if (lower.includes('delete') || lower.includes('remove')) return 'bg-red-500/15 text-red-700 dark:text-red-400';
  if (lower.includes('query') || lower.includes('search')) return 'bg-blue-500/15 text-blue-700 dark:text-blue-400';
  if (lower.includes('login') || lower.includes('auth')) return 'bg-slate-500/15 text-slate-700 dark:text-slate-400';
  return 'bg-violet-500/15 text-violet-700 dark:text-violet-400';
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDetails(details: Record<string, any> | null): string {
  if (!details) return '';
  const parts: string[] = [];
  if (details.filename) parts.push(details.filename);
  if (details.query) parts.push(`"${details.query}"`);
  if (details.doc_id) parts.push(`doc: ${details.doc_id}`);
  if (details.pages) parts.push(`${details.pages} pages`);
  if (parts.length > 0) return parts.join(' · ');
  return Object.entries(details)
    .filter(([, v]) => v != null && v !== '')
    .map(([k, v]) => `${k}: ${v}`)
    .slice(0, 3)
    .join(' · ');
}

export function ActivityLog() {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);

  const fetchLogs = useCallback(async (offset = 0, append = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getMyActivityLogs(PAGE_SIZE, offset);
      setLogs((prev) => (append ? [...prev, ...data] : data));
      setHasMore(data.length === PAGE_SIZE);
    } catch (err: any) {
      setError(err?.detail || 'Failed to load activity logs');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleLoadMore = () => {
    fetchLogs(logs.length, true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border/50">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigate('/app')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <Activity className="h-5 w-5 text-muted-foreground" />
        <h1 className="text-lg font-semibold">Activity Log</h1>
        <div className="flex-1" />
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => fetchLogs()}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-4 max-w-3xl mx-auto space-y-2">
          {/* Loading skeleton */}
          {isLoading && logs.length === 0 && (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Card key={i} className="border-border/40">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <Skeleton className="h-5 w-16 rounded-md" />
                      <Skeleton className="h-4 w-24" />
                      <div className="flex-1" />
                      <Skeleton className="h-4 w-16" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Error state */}
          {error && !isLoading && (
            <Card className="border-destructive/50">
              <CardContent className="p-6 text-center">
                <p className="text-sm text-destructive">{error}</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={() => fetchLogs()}>
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Empty state */}
          {!isLoading && !error && logs.length === 0 && (
            <Card className="border-border/40">
              <CardContent className="p-8 text-center">
                <Activity className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
                <p className="text-sm font-medium text-muted-foreground">No activity yet</p>
                <p className="text-xs text-muted-foreground/70 mt-1">
                  Your actions like uploads, queries, and logins will appear here.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Log entries */}
          {logs.map((log) => {
            const details = formatDetails(log.details);
            return (
              <Card key={log.log_id} className="border-border/40 hover:border-border/60 transition-colors">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-start gap-3">
                    <Badge
                      className={`${getActionColor(log.action)} border-0 text-[11px] font-medium shrink-0`}
                    >
                      {log.action}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm text-foreground">{log.resource_type}</span>
                        {log.resource_id && (
                          <span className="text-xs text-muted-foreground font-mono truncate max-w-[200px]">
                            {log.resource_id}
                          </span>
                        )}
                      </div>
                      {details && (
                        <p className="text-xs text-muted-foreground mt-1 truncate">{details}</p>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs text-muted-foreground">{formatTime(log.logged_at)}</span>
                      {log.ip_address && (
                        <p className="text-[10px] text-muted-foreground/60 mt-0.5">{log.ip_address}</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {/* Load more */}
          {hasMore && logs.length > 0 && (
            <div className="text-center py-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleLoadMore}
                disabled={isLoading}
              >
                {isLoading ? 'Loading...' : 'Load more'}
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
