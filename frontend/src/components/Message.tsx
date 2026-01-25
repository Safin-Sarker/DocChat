import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, FileText } from 'lucide-react';
import type { Message as MessageType } from '@/types/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface MessageProps {
  message: MessageType;
}

export const Message = ({ message }: MessageProps) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex gap-4 mb-6 ${
        isUser ? 'justify-end' : 'justify-start'
      } animate-in fade-in-50 slide-in-from-bottom-2 duration-300`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center ring-2 ring-primary/20">
          <Bot className="w-5 h-5 text-primary" />
        </div>
      )}

      <Card
        className={`max-w-[80%] ${
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-card'
        } shadow-md hover:shadow-lg transition-shadow duration-200`}
      >
        <div className="p-4 space-y-3">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                code({ inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-md text-sm"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code
                      className={`${
                        isUser ? 'bg-primary-foreground/20' : 'bg-muted'
                      } px-1.5 py-0.5 rounded text-sm font-mono`}
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {!isUser && message.sources && message.sources.length > 0 && (
            <>
              <Separator className="my-3" />
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <FileText className="w-4 h-4" />
                  <span>Sources ({message.sources.length})</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {message.sources.slice(0, 3).map((source, idx) => (
                    <Badge
                      key={idx}
                      variant="secondary"
                      className="text-xs cursor-pointer hover:bg-secondary/80 transition-colors"
                    >
                      {source.page ? `Page ${source.page}` : `Source ${idx + 1}`}
                    </Badge>
                  ))}
                  {message.sources.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{message.sources.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            </>
          )}

          {!isUser && message.contexts && message.contexts.length > 0 && (
            <details className="group">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground transition-colors list-none">
                <span className="inline-flex items-center gap-1">
                  <span className="group-open:rotate-90 transition-transform">▶</span>
                  View context ({message.contexts.length})
                </span>
              </summary>
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
            </details>
          )}
        </div>
      </Card>

      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-accent flex items-center justify-center ring-2 ring-border">
          <User className="w-5 h-5 text-accent-foreground" />
        </div>
      )}
    </div>
  );
};
