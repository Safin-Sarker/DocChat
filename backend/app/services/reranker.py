"""Reranker wrapper using OpenAI embeddings."""

from typing import List, Dict, Any
from math import sqrt
from openai import OpenAI
from app.core.config import settings


class Reranker:
    """Rerank candidate chunks using OpenAI embeddings when available."""

    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as exc:
                print(f"OpenAI client init failed: {exc}")

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sqrt(sum(a * a for a in vec_a))
        norm_b = sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank documents by relevance."""
        if not docs:
            return []

        if not self.openai_client:
            return docs[:top_k]

        try:
            return await self._rerank_with_openai(query, docs, top_k)
        except Exception as exc:
            print(f"OpenAI reranking failed: {exc}")
            return docs[:top_k]

    async def _rerank_with_openai(
        self, query: str, docs: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        texts = [doc.get("text", "") for doc in docs]
        response = self.openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=[query] + texts,
        )
        query_vec = response.data[0].embedding
        doc_vecs = [item.embedding for item in response.data[1:]]
        scores = [
            self._cosine_similarity(query_vec, doc_vec)
            for doc_vec in doc_vecs
        ]
        ranked_indices = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
        return [docs[i] for i in ranked_indices[:top_k]]
