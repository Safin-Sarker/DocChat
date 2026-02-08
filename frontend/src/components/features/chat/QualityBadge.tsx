import { useState } from 'react';
import { ShieldCheck, ShieldAlert, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react';
import type { ReflectionScore } from '@/types/api';
import { cn } from '@/lib/utils';

interface QualityBadgeProps {
  reflection?: ReflectionScore | null;
}

const DIMENSIONS: { key: keyof ReflectionScore; label: string }[] = [
  { key: 'faithfulness', label: 'Faithfulness' },
  { key: 'relevance', label: 'Relevance' },
  { key: 'completeness', label: 'Completeness' },
  { key: 'coherence', label: 'Coherence' },
  { key: 'conciseness', label: 'Conciseness' },
];

function getColor(score: number) {
  if (score >= 0.8) return 'text-green-600 dark:text-green-400';
  if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-red-600 dark:text-red-400';
}

function getBarColor(score: number) {
  if (score >= 0.8) return 'bg-green-500';
  if (score >= 0.6) return 'bg-yellow-500';
  return 'bg-red-500';
}

function getBadgeBg(score: number) {
  if (score >= 0.8) return 'bg-green-50 border-green-200 dark:bg-green-950/30 dark:border-green-800';
  if (score >= 0.6) return 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950/30 dark:border-yellow-800';
  return 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800';
}

export function QualityBadge({ reflection }: QualityBadgeProps) {
  const [expanded, setExpanded] = useState(false);

  if (!reflection) return null;

  const pct = Math.round(reflection.overall * 100);
  const Icon = reflection.was_regenerated
    ? RefreshCw
    : reflection.verdict === 'pass'
      ? ShieldCheck
      : ShieldAlert;

  return (
    <div className="pt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium transition-colors',
          getBadgeBg(reflection.overall),
          getColor(reflection.overall),
        )}
      >
        <Icon className="h-3.5 w-3.5" />
        <span>Quality: {pct}%</span>
        {reflection.was_regenerated && (
          <span className="text-[10px] opacity-70">(improved)</span>
        )}
        {expanded ? (
          <ChevronDown className="h-3 w-3 ml-0.5" />
        ) : (
          <ChevronRight className="h-3 w-3 ml-0.5" />
        )}
      </button>

      {expanded && (
        <div className="mt-2 p-3 rounded-md border border-border/50 bg-muted/30 space-y-2.5">
          {DIMENSIONS.map(({ key, label }) => {
            const score = reflection[key] as number;
            return (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-24 shrink-0">
                  {label}
                </span>
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn('h-full rounded-full transition-all', getBarColor(score))}
                    style={{ width: `${Math.round(score * 100)}%` }}
                  />
                </div>
                <span className={cn('text-xs font-mono w-8 text-right', getColor(score))}>
                  {Math.round(score * 100)}%
                </span>
              </div>
            );
          })}

          {reflection.feedback && (
            <p className="text-xs text-muted-foreground pt-1 border-t border-border/50 leading-relaxed">
              {reflection.feedback}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
