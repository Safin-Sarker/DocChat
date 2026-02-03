import { Bot } from 'lucide-react';

export function TypingIndicator() {
  return (
    <div className="py-6 px-4 bg-[hsl(var(--message-assistant-bg))]">
      <div className="max-w-3xl mx-auto flex gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <Bot className="w-4 h-4 text-primary-foreground" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-3">
          <p className="font-medium text-sm text-foreground">DocChat</p>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-muted-foreground/60 typing-dot" />
            <span className="w-2 h-2 rounded-full bg-muted-foreground/60 typing-dot" />
            <span className="w-2 h-2 rounded-full bg-muted-foreground/60 typing-dot" />
            <span className="ml-2 text-sm text-muted-foreground">Thinking...</span>
          </div>
        </div>
      </div>
    </div>
  );
}
