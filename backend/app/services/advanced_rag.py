"""End-to-end RAG pipeline service."""

import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)
from app.services.hybrid_retrieval import HybridRetrieval
from app.services.reranker import Reranker
from app.services.context_assembler import ContextAssembler
from app.services.response_generator import ResponseGenerator
from app.services.entity_extractor import EntityExtractor
from app.services.query_router import QueryRouter
from app.services.answer_judge import AnswerJudge


class AdvancedRAGService:
    """Orchestrate retrieval, reranking, and response generation."""

    def __init__(
        self,
        retrieval: HybridRetrieval | None = None,
        reranker: Reranker | None = None,
        assembler: ContextAssembler | None = None,
        generator: ResponseGenerator | None = None,
        entity_extractor: EntityExtractor | None = None,
        query_router: QueryRouter | None = None,
    ):
        self.retrieval = retrieval or HybridRetrieval()
        self.reranker = reranker or Reranker()
        self.assembler = assembler or ContextAssembler()
        self.generator = generator or ResponseGenerator()
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.query_router = query_router or QueryRouter()
        self.answer_judge = AnswerJudge() if settings.JUDGE_ENABLED else None

    async def answer(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """Generate an answer with sources and entities.

        Args:
            query: User's question
            user_id: User ID for multi-tenant isolation
            chat_history: Previous conversation messages for follow-up context
        """
        # Route query by intent
        intent = self.query_router.classify(query)

        if intent in ("greeting", "chitchat"):
            logger.info(f"Routed to casual response (intent: {intent})")
            answer = self.query_router.generate_casual_response(query, chat_history=chat_history)
            return {
                "answer": answer,
                "contexts": [],
                "sources": [],
                "entities": [],
                "reflection": None,
            }

        if intent == "summary":
            logger.info("Routed to summary pipeline")
            return await self._generate_summary(query, user_id, chat_history=chat_history)

        # Document query - full RAG pipeline
        logger.info(f"Routed to RAG pipeline (intent: {intent})")
        logger.info(f"Retrieving candidates for: {query[:80]}")
        candidates = await self.retrieval.retrieve(query, user_id=user_id)
        logger.info(f"Retrieved {len(candidates)} candidates")

        # Filter out empty/low-content chunks
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 30]
        logger.info(f"After filtering low-content: {len(candidates)} candidates")

        reranked = await self.reranker.rerank(query, candidates, settings.RERANK_TOP_K)
        logger.info(f"Reranked to {len(reranked)} results")

        contexts = self.assembler.assemble(reranked)
        logger.info(f"Assembled {len(contexts)} contexts")

        answer = self.generator.generate(query, contexts, chat_history=chat_history)
        logger.info(f"Generated answer ({len(answer)} chars)")

        # Judge evaluation
        reflection = None
        if self.answer_judge:
            verdict = self.answer_judge.evaluate(query, contexts, answer)
            if verdict.verdict == "fail" and settings.JUDGE_MAX_RETRIES > 0:
                logger.info(f"Judge failed answer (overall={verdict.overall:.2f}), regenerating with feedback...")
                answer = self.generator.generate_with_feedback(
                    query, contexts, verdict.feedback, chat_history=chat_history
                )
                logger.info(f"Regenerated answer ({len(answer)} chars)")
                verdict = self.answer_judge.evaluate(query, contexts, answer)
                verdict.was_regenerated = True
            reflection = verdict.to_dict()

        # Extract entities from the answer for graph visualization
        entities = self._extract_entities(query, answer)
        logger.info(f"Extracted {len(entities)} entities")

        return {
            "answer": answer,
            "contexts": contexts,
            "sources": [doc.get("metadata", {}) for doc in reranked],
            "entities": entities,
            "reflection": reflection,
        }

    async def _generate_summary(self, query: str, user_id: Optional[str] = None, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """Generate a document summary using content from early pages."""
        # Retrieve chunks from the beginning of the document (intro, abstract, TOC)
        summary_query = "introduction abstract overview purpose scope objectives table of contents"
        logger.info("Summary: retrieving intro/overview chunks...")
        candidates = await self.retrieval.retrieve(summary_query, user_id=user_id)
        logger.info(f"Summary: retrieved {len(candidates)} raw candidates")

        # Filter out empty chunks and prefer early pages
        candidates = [c for c in candidates if len(c.get("text", "").strip()) > 30]
        candidates.sort(key=lambda c: c.get("metadata", {}).get("page", 999))

        # Take the first 10 content-rich chunks (early pages)
        top_candidates = candidates[:10]
        logger.info(f"Summary: using {len(top_candidates)} chunks from pages {[c.get('metadata', {}).get('page', '?') for c in top_candidates]}")

        if not top_candidates:
            return {
                "answer": "I couldn't find enough content to generate a summary. Try asking a specific question about the document.",
                "contexts": [],
                "sources": [],
                "entities": [],
                "reflection": None,
            }

        contexts = self.assembler.assemble(top_candidates)
        logger.info(f"Summary: assembled {len(contexts)} contexts")

        summary_prompt = (
            "Provide a comprehensive summary and overview of this document. "
            "Cover the main topics, purpose, and key points."
        )
        answer = self.generator.generate(summary_prompt, contexts, chat_history=chat_history)
        logger.info(f"Generated summary ({len(answer)} chars)")

        # Judge evaluation
        reflection = None
        if self.answer_judge:
            verdict = self.answer_judge.evaluate(summary_prompt, contexts, answer)
            if verdict.verdict == "fail" and settings.JUDGE_MAX_RETRIES > 0:
                logger.info(f"Judge failed summary (overall={verdict.overall:.2f}), regenerating with feedback...")
                answer = self.generator.generate_with_feedback(
                    summary_prompt, contexts, verdict.feedback, chat_history=chat_history
                )
                logger.info(f"Regenerated summary ({len(answer)} chars)")
                verdict = self.answer_judge.evaluate(summary_prompt, contexts, answer)
                verdict.was_regenerated = True
            reflection = verdict.to_dict()

        entities = self._extract_entities(query, answer)

        return {
            "answer": answer,
            "contexts": contexts,
            "sources": [doc.get("metadata", {}) for doc in top_candidates],
            "entities": entities,
            "reflection": reflection,
        }

    def _extract_entities(self, query: str, answer: str) -> List[str]:
        """Extract entities from query and answer for graph visualization."""
        combined_text = f"{query}\n{answer}"
        return self.entity_extractor.extract_entities(combined_text)
