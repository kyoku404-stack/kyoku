import React from 'react';
import type { Meeting } from '@/types/meeting';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Video, FileText, Sparkles, ExternalLink, Clock } from 'lucide-react';
import { formatDate } from '@/utils/formatters';

interface MeetingListProps {
  meetings: Meeting[];
  loading?: boolean;
  onSelectMeeting?: (meeting: Meeting) => void;
}

export const MeetingList: React.FC<MeetingListProps> = ({
  meetings,
  loading = false,
  onSelectMeeting,
}) => {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse h-28 bg-muted/40" />
        ))}
      </div>
    );
  }

  if (!meetings.length) {
    return (
      <Card className="p-8 text-center text-muted-foreground border-dashed">
        <Video className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="font-medium text-lg text-foreground">No meetings logged</p>
        <p className="text-sm mt-1">Scheduled meetings, transcripts, and AI-extracted summaries will appear here.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {meetings.map((meeting) => (
        <Card
          key={meeting.id}
          className="hover:border-primary/40 transition-all cursor-pointer group"
          onClick={() => onSelectMeeting?.(meeting)}
        >
          <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-blue-500/10 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                <Video className="w-4 h-4" />
              </div>
              <div>
                <CardTitle className="text-sm font-semibold">{meeting.title}</CardTitle>
                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(meeting.scheduled_start)}
                  </span>
                  <span>•</span>
                  <span>Organizer ID: {meeting.organizer_id.slice(0, 8)}...</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {meeting.recording_url && (
                <a
                  href={meeting.recording_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  Recording <ExternalLink className="w-3 h-3" />
                </a>
              )}
              {meeting.summary_text ? (
                <Badge variant="success" className="flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> AI Summarized
                </Badge>
              ) : meeting.transcript_text ? (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <FileText className="w-3 h-3" /> Transcribed
                </Badge>
              ) : (
                <Badge variant="outline">Scheduled</Badge>
              )}
            </div>
          </CardHeader>

          {meeting.summary_text && (
            <CardContent className="py-2 px-4 border-t border-border/50 text-xs text-muted-foreground bg-muted/20">
              <p className="line-clamp-2">
                <span className="font-semibold text-foreground">AI Summary: </span>
                {meeting.summary_text}
              </p>
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  );
};
