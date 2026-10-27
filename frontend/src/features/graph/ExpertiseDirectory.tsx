/**
 * KEEP Enterprise Platform — ExpertiseDirectory Component (Phase 2.4).
 *
 * Subject-matter expertise discovery directory ranking organizational personnel
 * by co-occurrence scoring, document authorship, and project contributions.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Award,
  Search,
  FileText,
  Briefcase,
  UserCheck,
  Sparkles,
} from 'lucide-react';
import type { ExpertiseResponse } from '@/types/graph';

interface ExpertiseDirectoryProps {
  expertise: ExpertiseResponse | null;
  onSearchTopic: (topic: string) => void;
  loading?: boolean;
}

const POPULAR_TOPICS = [
  'Cybersecurity',
  'Cloud Architecture',
  'Intelligence',
  'Compliance & GDPR',
  'Machine Learning',
  'DevOps',
];

export const ExpertiseDirectory: React.FC<ExpertiseDirectoryProps> = ({
  expertise,
  onSearchTopic,
  loading = false,
}) => {
  const [topicInput, setTopicInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topicInput.trim()) {
      onSearchTopic(topicInput.trim());
    }
  };

  const handleChipClick = (t: string) => {
    setTopicInput(t);
    onSearchTopic(t);
  };

  return (
    <Card className="flex flex-col border-border bg-card shadow-xs" data-testid="expertise-directory">
      <CardHeader className="pb-3 border-b border-border space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
              <Award className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm font-bold text-foreground">
                Subject-Matter Expertise Discovery
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Find personnel with authoritative knowledge and document citations
              </p>
            </div>
          </div>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search topic or skill (e.g. 'Cybersecurity', 'Cloud Architecture')..."
              value={topicInput}
              onChange={(e) => setTopicInput(e.target.value)}
              className="pl-8 h-8 text-xs"
              data-testid="expertise-search-input"
            />
          </div>
          <Button type="submit" size="sm" className="h-8 text-xs gap-1.5" disabled={!topicInput.trim() || loading}>
            <UserCheck className="h-3.5 w-3.5" />
            Find Experts
          </Button>
        </form>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[10px] text-muted-foreground font-medium flex items-center gap-1">
            <Sparkles className="h-2.5 w-2.5 text-amber-500" /> Suggestions:
          </span>
          {POPULAR_TOPICS.map((top) => (
            <button
              key={top}
              type="button"
              onClick={() => handleChipClick(top)}
              className="rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[10px] font-medium text-muted-foreground hover:bg-primary/10 hover:text-primary transition-all"
            >
              {top}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-3">
        {loading && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-xs text-muted-foreground">
            <div className="h-6 w-6 rounded-full border-2 border-primary border-t-transparent animate-spin mb-2" />
            Ranking expert personnel...
          </div>
        )}

        {!loading && (!expertise || expertise.experts.length === 0) && (
          <div className="py-8 text-center text-xs text-muted-foreground">
            Enter a topic above or click a suggestion chip to discover organizational subject-matter experts.
          </div>
        )}

        {!loading && expertise && expertise.experts.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Showing top experts in <strong className="text-foreground">&ldquo;{expertise.topic}&rdquo;</strong>
              </span>
              <span className="text-[11px] font-medium">{expertise.experts.length} specialists found</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {expertise.experts.map((exp, idx) => (
                <div
                  key={exp.user_id}
                  className="flex flex-col p-3 rounded-lg border border-border bg-card/80 hover:border-primary/40 transition-all space-y-2 shadow-xs"
                  data-testid={`expert-card-${idx}`}
                >
                  {/* Expert Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 font-bold text-xs text-primary">
                        {exp.full_name.charAt(0)}
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-xs font-bold text-foreground truncate" title={exp.full_name}>
                          {exp.full_name}
                        </h4>
                        <span className="text-[11px] text-muted-foreground">
                          {exp.department || 'Enterprise'}
                        </span>
                      </div>
                    </div>
                    {/* Score Badge */}
                    <Badge variant="secondary" className="text-[10px] font-bold px-2 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shrink-0">
                      {exp.score.toFixed(1)} / 10
                    </Badge>
                  </div>

                  {/* Metrics */}
                  <div className="flex items-center gap-3 text-[11px] text-muted-foreground pt-1 border-t border-border">
                    <span className="flex items-center gap-1 font-medium">
                      <FileText className="h-3 w-3 text-amber-500" />
                      {exp.authored_documents_count} docs authored
                    </span>
                    <span className="flex items-center gap-1 font-medium">
                      <Briefcase className="h-3 w-3 text-purple-500" />
                      {exp.contributed_projects.length} projects
                    </span>
                  </div>

                  {/* Contributed Projects */}
                  {exp.contributed_projects.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {exp.contributed_projects.slice(0, 3).map((proj) => (
                        <Badge key={proj} variant="outline" className="text-[9px] px-1.5 py-0 font-normal">
                          {proj}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {/* Citations */}
                  {exp.evidence_citations.length > 0 && (
                    <div className="text-[10px] text-muted-foreground italic truncate">
                      Citations: {exp.evidence_citations.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
