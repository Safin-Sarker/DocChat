"""LLM response generation."""

from typing import List, Optional, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.config import settings


class ResponseGenerator:
    """Generate answers with retrieved context."""

    def __init__(self):
        self.client = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def _build_messages(self, prompt: str, chat_history: Optional[List] = None) -> list:
        """Build message list from prompt and chat history."""
        messages = [SystemMessage(content="You are DocChat, a helpful document Q&A assistant.")]
        for msg in (chat_history or []):
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=prompt))
        return messages

    def _build_prompt(self, query: str, contexts: List[str], feedback: str = "") -> str:
        """Build the prompt from query, contexts, and optional feedback."""
        context_text = "\n\n".join(contexts)
        prompt = (
            "Answer the user's question using the provided context from their uploaded documents.\n\n"
            "Guidelines:\n"
            "- Use the context to provide a thorough, helpful answer.\n"
            "- The context may come from MULTIPLE different documents. If so, cover information from ALL documents, not just one.\n"
            "- For broad questions like 'tell me about the documents' or 'summarize', "
            "provide an overview of each document separately, then highlight connections if any.\n"
            "- If the context doesn't fully answer the question, share what you can "
            "from the context and suggest the user ask a more specific question.\n"
            "- Never say you have no information if context is provided — always try to extract something useful.\n"
            "- Use the conversation history to understand follow-up questions and references like 'that', 'it', 'more', etc.\n\n"
        )
        if feedback:
            prompt += (
                f"IMPORTANT — A quality review found issues with a previous attempt. "
                f"Improve your answer based on this feedback:\n{feedback}\n\n"
            )
        prompt += f"Context:\n{context_text}\n\nQuestion:\n{query}"
        return prompt

    def generate(self, query: str, contexts: List[str], chat_history: Optional[List] = None) -> str:
        """Generate a response using the LLM with conversation history."""
        prompt = self._build_prompt(query, contexts)
        messages = self._build_messages(prompt, chat_history)
        response = self.client.invoke(messages)
        return response.content or ""

    def generate_with_feedback(
        self, query: str, contexts: List[str], feedback: str, chat_history: Optional[List] = None
    ) -> str:
        """Regenerate a response incorporating judge feedback."""
        prompt = self._build_prompt(query, contexts, feedback=feedback)
        messages = self._build_messages(prompt, chat_history)
        response = self.client.invoke(messages)
        return response.content or ""

    async def generate_stream(self, query: str, contexts: List[str], chat_history: Optional[List] = None) -> AsyncIterator[str]:
        """Stream a response token-by-token using async LLM streaming."""
        prompt = self._build_prompt(query, contexts)
        messages = self._build_messages(prompt, chat_history)
        async for chunk in self.client.astream(messages):
            if chunk.content:
                yield chunk.content

    async def generate_with_feedback_stream(
        self, query: str, contexts: List[str], feedback: str, chat_history: Optional[List] = None
    ) -> AsyncIterator[str]:
        """Stream a regenerated response incorporating judge feedback."""
        prompt = self._build_prompt(query, contexts, feedback=feedback)
        messages = self._build_messages(prompt, chat_history)
        async for chunk in self.client.astream(messages):
            if chunk.content:
                yield chunk.content

