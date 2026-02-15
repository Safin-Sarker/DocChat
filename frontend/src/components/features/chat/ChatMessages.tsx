import { useRef, useEffect, useState } from 'react';
import { ArrowDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MessageRow } from './MessageRow';
import { TypingIndicator } from './TypingIndicator';
import type { Message } from '@/types/api';
import { cn } from '@/lib/utils';

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  onRegenerate?: (messageId: string) => void;
}

export function ChatMessages({ messages, isLoading, onRegenerate }: ChatMessagesProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  // Auto-scroll on new messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check if scrolled up
  useEffect(() => {
    const scrollArea = scrollAreaRef.current;
    if (!scrollArea) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollArea;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isNearBottom);
    };

    scrollArea.addEventListener('scroll', handleScroll);
    return () => scrollArea.removeEventListener('scroll', handleScroll);
  }, []);

  // Find the last assistant message for regenerate button
  const lastAssistantIndex = messages.reduce(
    (lastIdx, m, idx) => (m.role === 'assistant' ? idx : lastIdx),
    -1
  );

  // Show typing indicator only when loading and the last message has no content yet
  const lastMessage = messages[messages.length - 1];
  const showTyping = isLoading && (!lastMessage || !lastMessage.content);

  return (
    <div className="relative flex-1 overflow-hidden">
      <div
        ref={scrollAreaRef}
        className="h-full overflow-y-auto scrollbar-thin"
      >
        <div>
          <div className="h-2" />
          {messages.map((message, index) => (
            <MessageRow
              key={message.id}
              message={message}
              onRegenerate={
                index === lastAssistantIndex && onRegenerate
                  ? () => onRegenerate(message.id)
                  : undefined
              }
              showRegenerate={index === lastAssistantIndex && !isLoading}
            />
          ))}
          {showTyping && <TypingIndicator />}
        </div>
        <div ref={messagesEndRef} className="h-1" />
      </div>

      {/* Jump to latest button */}
      <Button
        variant="secondary"
        size="sm"
        className={cn(
          'absolute bottom-4 left-1/2 -translate-x-1/2 shadow-lg transition-all duration-200 rounded-full px-4',
          showScrollButton
            ? 'opacity-100 translate-y-0'
            : 'opacity-0 translate-y-4 pointer-events-none'
        )}
        onClick={() => scrollToBottom()}
      >
        <ArrowDown className="h-4 w-4 mr-1" />
        Jump to latest
      </Button>
    </div>
  );
}
