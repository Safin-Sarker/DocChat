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
            "Answer the user's question using the provided context from their uploaded document.\n\n"
            "Guidelines:\n"
            "- Use the context to provide a thorough, helpful answer.\n"
            "- For broad questions like 'tell me about the document' or 'summarize', "
            "provide an overview based on the available context.\n"
            "- If the context doesn't fully answer the question, share what you can "
            "from the context and suggest the user ask a more specific question.\n"
            "- Never say you have no information if context is provided — always try to extract something useful.\n\n"
            f"Context:\n{context_text}\n\nQuestion:\n{query}"
        )

        response = self.client.invoke([
            SystemMessage(content="You are DocChat, a helpful document Q&A assistant."),
            HumanMessage(content=prompt)
        ])
        return response.content or ""
