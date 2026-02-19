import { Bot } from 'lucide-react';
import { useAppSelector } from '@/infrastructure/store/hooks';
import type { SSEStage } from '@/domain/query/types';

const STAGE_LABELS: Record<SSEStage, string> = {
  routing: 'Analyzing query...',
  retrieving: 'Searching documents...',
  reranking: 'Ranking results...',
  generating: 'Generating answer...',
  evaluating: 'Evaluating quality...',
  improving: 'Improving answer...',
  extracting: 'Extracting entities...',
};

export function TypingIndicator() {
  const streamingStage = useAppSelector((s) => s.chat.streamingStage);
  const label = streamingStage ? STAGE_LABELS[streamingStage] || 'Processing...' : 'Thinking...';

  return (
    <div className="py-4 px-4">
      <div className="max-w-3xl mx-auto flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
            <Bot className="w-3.5 h-3.5 text-primary" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          <p className="text-xs text-muted-foreground">DocChat</p>
          <div className="inline-flex items-center gap-1.5 bg-muted/50 rounded-full px-3 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 typing-dot" />
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 typing-dot" />
            <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 typing-dot" />
            <span className="ml-1.5 text-sm text-muted-foreground">{label}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
