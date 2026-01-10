"""LLM response generation."""

from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings


class ResponseGenerator:
    """Generate answers with retrieved context."""

    def __init__(self):
        self.client = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def generate(self, query: str, contexts: List[str]) -> str:
        """Generate a response using the LLM."""
        context_text = "\n\n".join(contexts)
        prompt = (
            "Answer the user question using the provided context. "
            "If the context is insufficient, say so.\n\n"
            f"Context:\n{context_text}\n\nQuestion:\n{query}"
        )

        response = self.client.invoke([
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=prompt)
        ])
        return response.content or ""
