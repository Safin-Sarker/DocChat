import { useEffect } from 'react';
import { useRAGQueryStream } from '@/application/query/useRAGQueryStream';
import { useAppSelector, useAppDispatch } from '@/infrastructure/store/hooks';
import { addMessage, setLoading, truncateMessagesAt } from '@/infrastructure/store/slices/chatSlice';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { WelcomeScreen } from './WelcomeScreen';

export function ChatContainer() {
  const messages = useAppSelector((s) => s.chat.messages);
  const selectedDocIds = useAppSelector((s) => s.chat.selectedDocIds);
  const selectAllDocs = useAppSelector((s) => s.chat.selectAllDocs);
  const isLoading = useAppSelector((s) => s.chat.isLoading);
  const uploadedDocuments = useAppSelector((s) => s.chat.uploadedDocuments);
  const dispatch = useAppDispatch();
  const { streamQuery } = useRAGQueryStream();

  // Safety: clear stuck loading state on mount (e.g. after page refresh)
  useEffect(() => {
    if (isLoading) {
      dispatch(setLoading(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const hasDocsSelected = selectedDocIds.length > 0;

  const handleSubmit = async (userMessage: string) => {
    if (!hasDocsSelected) return;

    // Add user message
    dispatch(addMessage({
      role: 'user',
      content: userMessage,
    }));

    // Add placeholder assistant message
    dispatch(addMessage({
      role: 'assistant',
      content: '',
    }));

    dispatch(setLoading(true));

    // Build chat history from recent messages (max 10) for follow-up context
    const recentHistory = messages
      .filter((m) => m.content) // skip empty placeholder messages
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    // Stream query — send empty doc_ids when all docs selected to search everything
    const effectiveDocIds = selectAllDocs
      ? uploadedDocuments.map((doc) => doc.doc_id)
      : selectedDocIds;

    await streamQuery({
      query: userMessage,
      chat_history: recentHistory,
      doc_ids: effectiveDocIds.length > 0 ? effectiveDocIds : undefined,
    });
  };

  const handleRegenerate = (messageId: string) => {
    // Find the user message before this assistant message
    const messageIndex = messages.findIndex((m) => m.id === messageId);
    if (messageIndex <= 0) return;

    const userMessage = messages[messageIndex - 1];
    if (userMessage.role !== 'user') return;

    // Remove the current assistant message and regenerate
    dispatch(truncateMessagesAt(messageIndex));

    // Resubmit the user message
    handleSubmit(userMessage.content);
  };

  // Show welcome screen if no messages
  if (messages.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <WelcomeScreen hasDocument={hasDocsSelected} hasUploadedDocs={uploadedDocuments.length > 0} />
        {hasDocsSelected && (
          <ChatInput
            onSubmit={handleSubmit}
            disabled={!hasDocsSelected}
            isLoading={isLoading}
          />
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        onRegenerate={handleRegenerate}
      />
      <ChatInput
        onSubmit={handleSubmit}
        disabled={!hasDocsSelected}
        isLoading={isLoading}
      />
    </div>
  );
}
