"""End-to-end RAG pipeline service."""

from typing import Dict, Any
from app.core.config import settings
from app.services.hybrid_retrieval import HybridRetrieval
from app.services.reranker import Reranker
from app.services.context_assembler import ContextAssembler
from app.services.response_generator import ResponseGenerator


class AdvancedRAGService:
    """Orchestrate retrieval, reranking, and response generation."""

    def __init__(
        self,
        retrieval: HybridRetrieval | None = None,
        reranker: Reranker | None = None,
        assembler: ContextAssembler | None = None,
        generator: ResponseGenerator | None = None,
    ):
        self.retrieval = retrieval or HybridRetrieval()
        self.reranker = reranker or Reranker()
        self.assembler = assembler or ContextAssembler()
        self.generator = generator or ResponseGenerator()

    async def answer(self, query: str) -> Dict[str, Any]:
        """Generate an answer with sources."""
        candidates = await self.retrieval.retrieve(query)
        reranked = await self.reranker.rerank(query, candidates, settings.RERANK_TOP_K)
        contexts = self.assembler.assemble(reranked)
        answer = self.generator.generate(query, contexts)

        return {
            "answer": answer,
            "contexts": contexts,
            "sources": [doc.get("metadata", {}) for doc in reranked]
        }
