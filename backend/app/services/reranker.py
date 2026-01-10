"""Cohere reranker wrapper with LangChain integration."""

from typing import List, Dict, Any
import cohere
from langchain_core.documents import Document
from app.core.config import settings


class Reranker:
    """Rerank candidate chunks using Cohere if available."""

    def __init__(self):
        self.client = None
        self.lc_reranker = None
        try:
            from langchain.retrievers.document_compressors import CohereRerank
            self.lc_reranker = CohereRerank(
                cohere_api_key=settings.COHERE_API_KEY,
                top_n=settings.RERANK_TOP_K
            )
        except Exception as exc:
            print(f"LangChain CohereRerank unavailable: {exc}")

        if settings.COHERE_API_KEY:
            try:
                self.client = cohere.Client(settings.COHERE_API_KEY)
            except Exception as exc:
                print(f"Cohere client init failed: {exc}")

    async def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank documents by relevance."""
        if not docs:
            return []

        if self.lc_reranker:
            try:
                documents = [
                    Document(page_content=doc.get("text", ""), metadata=doc.get("metadata", {}))
                    for doc in docs
                ]
                compressed = self.lc_reranker.compress_documents(documents, query=query)
                id_lookup = {doc.get("text", ""): doc for doc in docs}
                ranked = []
                for doc in compressed:
                    ranked.append(id_lookup.get(doc.page_content, {"text": doc.page_content}))
                return ranked[:top_k]
            except Exception as exc:
                print(f"LangChain reranking failed: {exc}")

        if not self.client:
            return docs[:top_k]

        try:
            texts = [doc.get("text", "") for doc in docs]
            response = self.client.rerank(query=query, documents=texts, top_n=top_k)
            ranked = []
            for result in response.results:
                ranked.append(docs[result.index])
            return ranked
        except Exception as exc:
            print(f"Reranking failed: {exc}")
            return docs[:top_k]
