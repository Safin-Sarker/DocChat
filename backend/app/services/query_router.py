"""LLM-based query router to classify intent before processing."""

import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

ROUTER_PROMPT = """Classify the user's message intent. Return JSON with key "intent" set to one of:
- "greeting": casual greetings, hello, hi, hey, etc.
- "chitchat": casual conversation, thanks, goodbye, how are you, etc.
- "summary": broad requests about the document overview, summary, what it's about, its content, main topics.
- "document_query": a specific question that requires searching documents for information.

Only return the JSON object, no extra text.

Examples:
User: "Hi" -> {"intent": "greeting"}
User: "Thanks!" -> {"intent": "chitchat"}
User: "What are the side effects?" -> {"intent": "document_query"}
User: "Summarize page 5" -> {"intent": "document_query"}
User: "Hello, how are you?" -> {"intent": "greeting"}
User: "What does the document say about training?" -> {"intent": "document_query"}
User: "Tell me about the document" -> {"intent": "summary"}
User: "What is this document about?" -> {"intent": "summary"}
User: "Give me an overview" -> {"intent": "summary"}
User: "Summarize the document" -> {"intent": "summary"}
User: "What are the main topics?" -> {"intent": "summary"}
User: "I want to know about the content" -> {"intent": "summary"}
"""


class QueryRouter:
    """Route queries based on intent classification."""

    def __init__(self):
        self.client = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def classify(self, query: str) -> str:
        """Classify query intent.

        Returns:
            One of: "greeting", "chitchat", "document_query"
        """
        try:
            response = self.client.invoke([
                SystemMessage(content=ROUTER_PROMPT),
                HumanMessage(content=query)
            ])
            data = json.loads(response.content or "{}")
            intent = data.get("intent", "document_query")
            logger.info(f"Query router: '{query[:50]}' -> {intent}")
            return intent
        except Exception as exc:
            logger.warning(f"Query router failed, defaulting to document_query: {exc}")
            return "document_query"

    def generate_casual_response(self, query: str) -> str:
        """Generate a direct response for non-document queries."""
        response = self.client.invoke([
            SystemMessage(content=(
                "You are DocChat, a friendly document Q&A assistant. "
                "Respond briefly to the user's message. "
                "If they greet you, greet them back and let them know you're ready to help with their documents."
            )),
            HumanMessage(content=query)
        ])
        return response.content or ""
