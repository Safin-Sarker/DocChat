import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, Copy, Check, FileText, ChevronDown, ChevronRight, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import type { Message } from '@/types/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
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

  return (
    <div
      className={cn(
        'group py-6 px-4',
        isUser ? 'bg-transparent' : 'bg-[hsl(var(--message-assistant-bg))]'
      )}
    >
      <div className="max-w-3xl mx-auto flex gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center',
              isUser ? 'bg-primary/10' : 'bg-primary'
            )}
          >
            {isUser ? (
              <User className="w-4 h-4 text-primary" />
            ) : (
              <Bot className="w-4 h-4 text-primary-foreground" />
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Name */}
          <p className="font-medium text-sm text-foreground">
            {isUser ? 'You' : 'DocChat'}
          </p>

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
          {!isUser && message.sources && message.sources.length > 0 && (
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
          {!isUser && <QualityBadge reflection={message.reflection} />}

          {/* Context (collapsible) */}
          {!isUser && message.contexts && message.contexts.length > 0 && (
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
          {!isUser && message.content && (
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
