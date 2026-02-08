"""LLM response generation."""

from typing import List, Optional
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

    def generate(self, query: str, contexts: List[str], chat_history: Optional[List] = None) -> str:
        """Generate a response using the LLM with conversation history."""
        context_text = "\n\n".join(contexts)
        prompt = (
            "Answer the user's question using the provided context from their uploaded document.\n\n"
            "Guidelines:\n"
            "- Use the context to provide a thorough, helpful answer.\n"
            "- For broad questions like 'tell me about the document' or 'summarize', "
            "provide an overview based on the available context.\n"
            "- If the context doesn't fully answer the question, share what you can "
            "from the context and suggest the user ask a more specific question.\n"
            "- Never say you have no information if context is provided — always try to extract something useful.\n"
            "- Use the conversation history to understand follow-up questions and references like 'that', 'it', 'more', etc.\n\n"
            f"Context:\n{context_text}\n\nQuestion:\n{query}"
        )

        messages = [SystemMessage(content="You are DocChat, a helpful document Q&A assistant.")]

        # Add conversation history for follow-up context
        for msg in (chat_history or []):
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=prompt))

        response = self.client.invoke(messages)
        return response.content or ""

    def generate_with_feedback(
        self, query: str, contexts: List[str], feedback: str, chat_history: Optional[List] = None
    ) -> str:
        """Regenerate a response incorporating judge feedback."""
        context_text = "\n\n".join(contexts)
        prompt = (
            "Answer the user's question using the provided context from their uploaded document.\n\n"
            "Guidelines:\n"
            "- Use the context to provide a thorough, helpful answer.\n"
            "- For broad questions like 'tell me about the document' or 'summarize', "
            "provide an overview based on the available context.\n"
            "- If the context doesn't fully answer the question, share what you can "
            "from the context and suggest the user ask a more specific question.\n"
            "- Never say you have no information if context is provided — always try to extract something useful.\n"
            "- Use the conversation history to understand follow-up questions and references like 'that', 'it', 'more', etc.\n\n"
            f"IMPORTANT — A quality review found issues with a previous attempt. "
            f"Improve your answer based on this feedback:\n{feedback}\n\n"
            f"Context:\n{context_text}\n\nQuestion:\n{query}"
        )

        messages = [SystemMessage(content="You are DocChat, a helpful document Q&A assistant.")]

        for msg in (chat_history or []):
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=prompt))

        response = self.client.invoke(messages)
        return response.content or ""
