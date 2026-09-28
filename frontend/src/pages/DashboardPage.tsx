import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Cpu, Database, Users, ArrowUpRight } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto py-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Enterprise Workspace Dashboard
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Knowledge indexing telemetry, processing queues, and active document nodes.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Ingested Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,248</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center text-emerald-600 dark:text-emerald-400">
              <ArrowUpRight className="h-3.5 w-3.5 mr-0.5" />
              +14% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Indexed Chunks</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">48,920</div>
            <p className="text-xs text-muted-foreground mt-1">
              pgvector 1536-dim embeddings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Knowledge Graph Nodes</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3,412</div>
            <p className="text-xs text-muted-foreground mt-1">
              8,109 semantic relationships
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Collaborators</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">84</div>
            <p className="text-xs text-muted-foreground mt-1">
              Across 5 departments
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Ingestion Queue</CardTitle>
            <CardDescription>Status of recent documents submitted to Celery</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-2.5 rounded-lg border border-border">
                <div className="flex items-center space-x-3">
                  <FileText className="h-4 w-4 text-primary" />
                  <div>
                    <div className="text-sm font-medium">Q3_Financial_Review.pdf</div>
                    <div className="text-xs text-muted-foreground">4.2 MB &bull; Finance</div>
                  </div>
                </div>
                <Badge variant="processed">PROCESSED</Badge>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg border border-border">
                <div className="flex items-center space-x-3">
                  <FileText className="h-4 w-4 text-primary" />
                  <div>
                    <div className="text-sm font-medium">Architecture_Blueprint_v2.docx</div>
                    <div className="text-xs text-muted-foreground">1.8 MB &bull; Engineering</div>
                  </div>
                </div>
                <Badge variant="processing">PROCESSING</Badge>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg border border-border">
                <div className="flex items-center space-x-3">
                  <FileText className="h-4 w-4 text-primary" />
                  <div>
                    <div className="text-sm font-medium">Annual_Security_Audit.pdf</div>
                    <div className="text-xs text-muted-foreground">8.4 MB &bull; Compliance</div>
                  </div>
                </div>
                <Badge variant="pending">PENDING</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Hybrid Search Distribution</CardTitle>
            <CardDescription>Vector vs Full-text search utilization</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Dense Semantic Retrieval (pgvector)</span>
                <span>68%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: '68%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Sparse Keyword BM25</span>
                <span>24%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-sky-500 rounded-full" style={{ width: '24%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Knowledge Graph Traversal</span>
                <span>8%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: '8%' }} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
