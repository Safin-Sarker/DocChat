"""LLM-as-a-Judge reflection layer for RAG answer quality evaluation."""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """\
You are an impartial quality judge for a document Q&A system.
Evaluate the ANSWER against the provided CONTEXT and QUESTION.

Score each dimension from 0.0 to 1.0:
- faithfulness: Does the answer only use information present in the context? (no hallucinations)
- relevance: Does the answer address the user's question?
- completeness: Does the answer cover the key points from the context?
- coherence: Is the answer well-structured and easy to follow?
- conciseness: Is the answer appropriately concise without unnecessary filler?

Respond ONLY with a JSON object (no markdown, no extra text):
{
  "faithfulness": <float>,
  "relevance": <float>,
  "completeness": <float>,
  "coherence": <float>,
  "conciseness": <float>,
  "feedback": "<brief explanation of any weaknesses>"
}"""


@dataclass
class JudgeVerdict:
    """Result of an LLM-as-a-Judge evaluation."""

    faithfulness: float = 1.0
    relevance: float = 1.0
    completeness: float = 1.0
    coherence: float = 1.0
    conciseness: float = 1.0
    overall: float = 1.0
    verdict: str = "pass"
    feedback: str = ""
    was_regenerated: bool = False

    def to_dict(self) -> dict:
        return {
            "faithfulness": self.faithfulness,
            "relevance": self.relevance,
            "completeness": self.completeness,
            "coherence": self.coherence,
            "conciseness": self.conciseness,
            "overall": self.overall,
            "verdict": self.verdict,
            "feedback": self.feedback,
            "was_regenerated": self.was_regenerated,
        }


class AnswerJudge:
    """Evaluate RAG answers using an LLM judge."""

    def __init__(self):
        self.client = ChatOpenAI(
            model=settings.JUDGE_MODEL,
            temperature=settings.JUDGE_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.threshold = settings.JUDGE_THRESHOLD

    def _compute_overall(self, scores: dict) -> float:
        """Weighted overall score: 30% faithfulness, 25% relevance, 20% completeness, 15% coherence, 10% conciseness."""
        return (
            0.30 * scores.get("faithfulness", 1.0)
            + 0.25 * scores.get("relevance", 1.0)
            + 0.20 * scores.get("completeness", 1.0)
            + 0.15 * scores.get("coherence", 1.0)
            + 0.10 * scores.get("conciseness", 1.0)
        )

    def evaluate(self, query: str, contexts: List[str], answer: str) -> JudgeVerdict:
        """Evaluate an answer against the query and contexts.

        Returns a JudgeVerdict with dimension scores, overall score, verdict, and feedback.
        On LLM failure, returns a neutral pass verdict.
        """
        start = time.time()
        try:
            context_text = "\n\n---\n\n".join(contexts) if contexts else "(no context)"
            user_prompt = (
                f"QUESTION:\n{query}\n\n"
                f"CONTEXT:\n{context_text}\n\n"
                f"ANSWER:\n{answer}"
            )

            messages = [
                SystemMessage(content=JUDGE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            response = self.client.invoke(messages)
            raw = response.content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            scores = json.loads(raw)
            overall = self._compute_overall(scores)
            verdict_str = "pass" if overall >= self.threshold else "fail"

            result = JudgeVerdict(
                faithfulness=scores.get("faithfulness", 1.0),
                relevance=scores.get("relevance", 1.0),
                completeness=scores.get("completeness", 1.0),
                coherence=scores.get("coherence", 1.0),
                conciseness=scores.get("conciseness", 1.0),
                overall=round(overall, 3),
                verdict=verdict_str,
                feedback=scores.get("feedback", ""),
            )

            elapsed = time.time() - start
            logger.info(
                f"Judge verdict: {result.verdict} (overall={result.overall:.2f}) in {elapsed:.1f}s"
            )
            return result

        except Exception as e:
            elapsed = time.time() - start
            logger.warning(f"Judge evaluation failed ({elapsed:.1f}s): {e}")
            return JudgeVerdict()
