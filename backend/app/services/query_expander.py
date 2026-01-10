"""Query expansion using LLM."""

from typing import List
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings


class QueryExpander:
    """Generate query expansions to improve recall."""

    def __init__(self):
        self.client = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def expand(self, query: str, max_expansions: int = 3) -> List[str]:
        """Return expanded queries including the original."""
        if not query.strip():
            return []

        prompt = (
            "Generate concise search query variations for the user question. "
            "Return JSON with key 'queries' as an array of strings. "
            f"Limit to {max_expansions} items. No extra text."
        )

        try:
            response = self.client.invoke([
                SystemMessage(content="You generate search queries."),
                HumanMessage(content=f"{prompt}\n\nQuestion:\n{query}")
            ])
            content = response.content or ""
            data = json.loads(content)
            queries = data.get("queries", [])
            cleaned = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
            return [query] + [q for q in cleaned if q != query]
        except Exception as exc:
            print(f"Query expansion failed: {exc}")
            return [query]
