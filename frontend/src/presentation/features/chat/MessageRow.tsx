import { useState, useCallback, useRef, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Bot, Copy, Check, FileText, ChevronDown, ChevronRight, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import type { Message } from '@/domain/chat/types';
import type { SourceMapEntry } from '@/domain/query/types';
import { Button } from '@/presentation/ui/button';
import { Badge } from '@/presentation/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/presentation/ui/tooltip';
import { QualityBadge } from './QualityBadge';

interface MessageRowProps {
  message: Message;
  onRegenerate?: () => void;
  showRegenerate?: boolean;
}

/**
 * Parse text and replace [N] citation patterns with clickable badges.
 */
function renderTextWithCitations(
  text: string,
  sourceMap: SourceMapEntry[] | undefined,
  onCitationClick: (index: number) => void
): ReactNode[] {
  if (!sourceMap || sourceMap.length === 0) {
    return [text];
  }

  const parts: ReactNode[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    const citationIndex = parseInt(match[1], 10);
    const entry = sourceMap.find((s) => s.index === citationIndex);

    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (entry) {
      parts.push(
        <button
          key={`cite-${match.index}`}
          className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 mx-0.5 text-[11px] font-medium bg-primary/15 text-primary rounded hover:bg-primary/25 transition-colors cursor-pointer align-baseline"
          title={`${entry.doc_name || 'Source'}${entry.page ? `, Page ${entry.page}` : ''}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onCitationClick(citationIndex);
          }}
        >
          {citationIndex}
        </button>
      );
    } else {
      parts.push(match[0]);
    }

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

export function MessageRow({ message, onRegenerate, showRegenerate }: MessageRowProps) {
  const [copied, setCopied] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [highlightedContext, setHighlightedContext] = useState<number | null>(null);
  const contextRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCitationClick = useCallback((index: number) => {
    // Expand context section if collapsed
    if (!showContext) {
      setShowContext(true);
    }
    setHighlightedContext(index);

    // Scroll to the context after a tick (to allow expansion)
    setTimeout(() => {
      const el = contextRefs.current[index];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, 100);

    // Clear highlight after 2 seconds
    setTimeout(() => setHighlightedContext(null), 2000);
  }, [showContext]);

  const sourceMap = message.source_map;

  // Build markdown components with citation support for assistant messages
  const buildMarkdownComponents = (isAssistant: boolean) => ({
    code({ inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      const codeString = String(children).replace(/\n$/, '');

      if (!inline && match) {
        return (
          <div className="relative group/code my-3">
            <div className="absolute right-2 top-2 opacity-0 group-hover/code:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="icon"
                className={`h-7 w-7 ${isAssistant ? 'bg-background/80 hover:bg-background' : 'bg-white/20 hover:bg-white/30'}`}
                onClick={() => {
                  navigator.clipboard.writeText(codeString);
                  toast.success('Code copied');
                }}
              >
                <Copy className="h-3.5 w-3.5" />
              </Button>
            </div>
            <SyntaxHighlighter
              style={oneDark}
              language={match[1]}
              PreTag="div"
              className="!rounded-lg !text-sm !my-0"
              {...props}
            >
              {codeString}
            </SyntaxHighlighter>
          </div>
        );
      }

      return (
        <code
          className={`${isAssistant ? 'bg-muted' : 'bg-white/20'} px-1.5 py-0.5 rounded-md text-sm font-mono`}
          {...props}
        >
          {children}
        </code>
      );
    },
    // For assistant messages, intercept text nodes to inject citation links
    ...(isAssistant && sourceMap && sourceMap.length > 0
      ? {
          p({ children, ...props }: any) {
            return <p {...props}>{processCitationChildren(children)}</p>;
          },
          li({ children, ...props }: any) {
            return <li {...props}>{processCitationChildren(children)}</li>;
          },
          strong({ children, ...props }: any) {
            return <strong {...props}>{processCitationChildren(children)}</strong>;
          },
          em({ children, ...props }: any) {
            return <em {...props}>{processCitationChildren(children)}</em>;
          },
        }
      : {}),
  });

  const processCitationChildren = (children: ReactNode): ReactNode => {
    if (!children) return children;
    if (typeof children === 'string') {
      return renderTextWithCitations(children, sourceMap, handleCitationClick);
    }
    if (Array.isArray(children)) {
      return children.map((child, i) => {
        if (typeof child === 'string') {
          const parts = renderTextWithCitations(child, sourceMap, handleCitationClick);
          return parts.length === 1 && typeof parts[0] === 'string' ? parts[0] : <span key={i}>{parts}</span>;
        }
        return child;
      });
    }
    return children;
  };

  if (isUser) {
    return (
      <div className="group py-4 px-4">
        <div className="max-w-3xl mx-auto flex justify-end">
          <div className="max-w-[85%] sm:max-w-[75%] bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5">
            <div className="prose-chat-user text-sm">
              <ReactMarkdown components={buildMarkdownComponents(false)}>
                {message.content || '...'}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group py-4 px-4">
      <div className="max-w-3xl mx-auto flex gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
            <Bot className="w-3.5 h-3.5 text-primary" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Name */}
          <p className="text-xs text-muted-foreground">DocChat</p>

          {/* Message content */}
          <div className="prose-chat text-sm">
            <ReactMarkdown components={buildMarkdownComponents(true)}>
              {message.content || '...'}
            </ReactMarkdown>
          </div>

          {/* Sources — numbered reference list when source_map is available */}
          {sourceMap && sourceMap.length > 0 ? (
            <div className="space-y-1 pt-2">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <FileText className="h-3 w-3" />
                References
              </span>
              <div className="flex flex-wrap gap-1.5">
                {sourceMap.map((entry) => (
                  <Badge
                    key={entry.index}
                    variant="secondary"
                    className="text-xs font-normal cursor-pointer hover:bg-primary/15 transition-colors"
                    onClick={() => handleCitationClick(entry.index)}
                  >
                    [{entry.index}] {entry.doc_name || 'Source'}{entry.page ? ` p.${entry.page}` : ''}
                  </Badge>
                ))}
              </div>
            </div>
          ) : message.sources && message.sources.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <FileText className="h-3 w-3" />
                Sources:
              </span>
              {message.sources.slice(0, 5).map((source, idx) => (
                <Badge
                  key={idx}
                  variant="secondary"
                  className="text-xs font-normal"
                >
                  {source.page ? `Page ${source.page}` : `Source ${idx + 1}`}
                </Badge>
              ))}
              {message.sources.length > 5 && (
                <Badge variant="outline" className="text-xs font-normal">
                  +{message.sources.length - 5} more
                </Badge>
              )}
            </div>
          ) : null}

          {/* Quality Badge */}
          <QualityBadge reflection={message.reflection} />
          {message.cache?.cache_hit && (
            <div className="pt-1">
              <Badge variant="outline" className="text-[11px] font-normal">
                Served from {message.cache.cache_type} cache
              </Badge>
            </div>
          )}

          {/* Context (collapsible) */}
          {message.contexts && message.contexts.length > 0 && (
            <div className="pt-2">
              <button
                onClick={() => setShowContext(!showContext)}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {showContext ? (
                  <ChevronDown className="h-3 w-3" />
                ) : (
                  <ChevronRight className="h-3 w-3" />
                )}
                View context ({message.contexts.length})
              </button>
              {showContext && (
                <div className="mt-2 space-y-2">
                  {message.contexts.map((context, idx) => {
                    // Extract the citation number from the context prefix (e.g., "[1] [Document: ...]")
                    const citationMatch = context.match(/^\[(\d+)\]/);
                    const citationIndex = citationMatch ? parseInt(citationMatch[1], 10) : null;
                    const isHighlighted = citationIndex !== null && highlightedContext === citationIndex;

                    return (
                      <div
                        key={idx}
                        ref={(el) => {
                          if (citationIndex !== null) {
                            contextRefs.current[citationIndex] = el;
                          }
                        }}
                        className={`text-xs p-3 rounded-md border leading-relaxed transition-all duration-300 ${
                          isHighlighted
                            ? 'bg-primary/10 border-primary/40 ring-1 ring-primary/30'
                            : 'bg-muted/50 border-border/50'
                        }`}
                      >
                        {context}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          {message.content && (
            <div className="flex gap-1 pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={handleCopy}
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Copy response</TooltipContent>
              </Tooltip>
              {showRegenerate && onRegenerate && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={onRegenerate}
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Regenerate response</TooltipContent>
                </Tooltip>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
