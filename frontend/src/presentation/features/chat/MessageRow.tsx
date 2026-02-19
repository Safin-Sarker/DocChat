import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Bot, Copy, Check, FileText, ChevronDown, ChevronRight, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import type { Message } from '@/domain/chat/types';
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

export function MessageRow({ message, onRegenerate, showRegenerate }: MessageRowProps) {
  const [copied, setCopied] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="group py-4 px-4">
        <div className="max-w-3xl mx-auto flex justify-end">
          <div className="max-w-[85%] sm:max-w-[75%] bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5">
            <div className="prose-chat-user text-sm">
              <ReactMarkdown
                components={{
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
                              className="h-7 w-7 bg-white/20 hover:bg-white/30"
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
                        className="bg-white/20 px-1.5 py-0.5 rounded-md text-sm font-mono"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                }}
              >
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
            <ReactMarkdown
              components={{
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
                            className="h-7 w-7 bg-background/80 hover:bg-background"
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
                      className="bg-muted px-1.5 py-0.5 rounded-md text-sm font-mono"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content || '...'}
            </ReactMarkdown>
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
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
          )}

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
                  {message.contexts.map((context, idx) => (
                    <div
                      key={idx}
                      className="text-xs p-3 bg-muted/50 rounded-md border border-border/50 leading-relaxed"
                    >
                      {context}
                    </div>
                  ))}
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
