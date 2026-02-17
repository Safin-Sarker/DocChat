import { useRAGQueryStream } from '@/hooks/useQuery';
import { useChatStore } from '@/stores/chatStore';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { WelcomeScreen } from './WelcomeScreen';

export function ChatContainer() {
  const {
    messages,
    addMessage,
    setLoading,
    selectedDocIds,
    selectAllDocs,
    isLoading,
    uploadedDocuments,
  } = useChatStore();
  const { streamQuery } = useRAGQueryStream();

  const hasDocsSelected = selectedDocIds.length > 0;

  const handleSubmit = async (userMessage: string) => {
    if (!hasDocsSelected) return;

    // Add user message
    addMessage({
      role: 'user',
      content: userMessage,
    });

    // Add placeholder assistant message
    addMessage({
      role: 'assistant',
      content: '',
    });

    setLoading(true);

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
    useChatStore.setState((state) => ({
      messages: state.messages.slice(0, messageIndex),
    }));

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
