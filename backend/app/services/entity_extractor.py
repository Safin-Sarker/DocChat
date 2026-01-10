"""Entity extraction using LLM."""

from typing import List
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings


class EntityExtractor:
    """Extract named entities from text using OpenAI."""

    def __init__(self):
        self.client = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def extract_entities(self, text: str) -> List[str]:
        """Extract entities from text and return a list of strings."""
        if not text.strip():
            return []

        prompt = (
            "Extract the key entities (people, organizations, products, "
            "concepts) from the text. Return JSON with key 'entities' "
            "as an array of strings. No extra text."
        )

        try:
            response = self.client.invoke([
                SystemMessage(content="You are a precise entity extractor."),
                HumanMessage(content=f"{prompt}\n\nText:\n{text}")
            ])
            content = response.content or ""
            data = json.loads(content)
            entities = data.get("entities", [])
            return [e.strip() for e in entities if isinstance(e, str) and e.strip()]
        except Exception as exc:
            print(f"Entity extraction failed: {exc}")
            return []
