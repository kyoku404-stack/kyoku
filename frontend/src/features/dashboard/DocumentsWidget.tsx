import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useRecentDocuments } from '@/hooks/useDashboard';
import { ROUTES } from '@/routes/paths';
import {
  FileText,
  FileCode,
  FileSpreadsheet,
  FileCheck,
  File,
  Sparkles,
  ArrowRight,
  RefreshCw,
  ExternalLink,
  Clock,
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

export const DocumentsWidget: React.FC = () => {
  const { documents, isLoading, error, refresh } = useRecentDocuments(8);

  const getFileIcon = (fileType: string) => {
    switch (fileType?.toLowerCase()) {
      case 'pdf':
        return <FileText className="h-4 w-4 text-rose-500" />;
      case 'docx':
      case 'doc':
        return <FileCheck className="h-4 w-4 text-blue-500" />;
      case 'xlsx':
      case 'csv':
        return <FileSpreadsheet className="h-4 w-4 text-emerald-500" />;
      case 'md':
      case 'txt':
        return <FileCode className="h-4 w-4 text-amber-500" />;
      default:
        return <File className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (!bytes || bytes === 0) return '0 KB';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(0)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  return (
    <Card className="border border-border bg-card flex flex-col h-full shadow-xs">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-foreground">
                Recent Documents
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Knowledge assets & documentation
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              onClick={refresh}
              disabled={isLoading}
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              aria-label="Refresh recent documents"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>

            <Link to={ROUTES.DOCUMENTS}>
              <Button variant="ghost" size="sm" className="h-7 text-xs gap-1 text-primary hover:text-primary">
                <span>View All</span>
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 overflow-y-auto max-h-[420px]">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3 animate-pulse">
                <div className="h-8 w-8 bg-muted rounded-lg shrink-0" />
                <div className="space-y-1.5 flex-1">
                  <div className="h-3.5 w-3/5 bg-muted rounded" />
                  <div className="h-3 w-2/5 bg-muted rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : error && documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <p>{error}</p>
            <Button size="sm" variant="outline" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-2">
            <FileText className="h-8 w-8 mx-auto text-muted-foreground/40 mb-1" />
            <p>No recent documents uploaded.</p>
            <Link to={ROUTES.UPLOAD}>
              <Button size="sm" variant="outline" className="mt-2 text-xs">
                Upload Knowledge File
              </Button>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-border/60">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3.5 hover:bg-muted/30 transition-colors gap-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted/60 shrink-0 border border-border/40">
                    {getFileIcon(doc.file_type)}
                  </div>

                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-foreground truncate max-w-[200px] sm:max-w-[260px]">
                        {doc.title}
                      </span>
                      {doc.ai_summary_available && (
                        <Badge variant="outline" className="text-[9px] px-1 py-0 gap-0.5 border-purple-500/30 text-purple-600 dark:text-purple-400 bg-purple-500/5">
                          <Sparkles className="h-2.5 w-2.5" />
                          <span>AI Ready</span>
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span className="uppercase text-[10px] font-medium text-muted-foreground">
                        {doc.file_type}
                      </span>
                      <span>•</span>
                      <span>{formatFileSize(doc.file_size_bytes)}</span>
                      {doc.project_name && (
                        <>
                          <span>•</span>
                          <span className="truncate max-w-[120px]">{doc.project_name}</span>
                        </>
                      )}
                      <span>•</span>
                      <span className="flex items-center gap-1 text-[10px]">
                        <Clock className="h-3 w-3" />
                        {formatDate(doc.last_accessed_at || doc.uploaded_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <Link to={ROUTES.DOCUMENTS} className="shrink-0">
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground">
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
