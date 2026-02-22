"""Tests for app.services.answer_judge — JudgeVerdict and score computation."""

from app.services.answer_judge import AnswerJudge, JudgeVerdict


def test_compute_overall_perfect_scores():
    """All 1.0 scores yield 1.0 overall."""
    judge = AnswerJudge.__new__(AnswerJudge)  # skip __init__ (avoids LLM client)
    scores = {
        "faithfulness": 1.0,
        "relevance": 1.0,
        "completeness": 1.0,
        "coherence": 1.0,
        "conciseness": 1.0,
    }
    overall = judge._compute_overall(scores)
    assert abs(overall - 1.0) < 1e-6


def test_compute_overall_weighted():
    """Verify weighted calculation matches expected value."""
    judge = AnswerJudge.__new__(AnswerJudge)
    scores = {
        "faithfulness": 0.8,
        "relevance": 0.6,
        "completeness": 0.4,
        "coherence": 0.2,
        "conciseness": 0.0,
    }
    # Default weights: 0.30, 0.25, 0.20, 0.15, 0.10
    expected = 0.30 * 0.8 + 0.25 * 0.6 + 0.20 * 0.4 + 0.15 * 0.2 + 0.10 * 0.0
    overall = judge._compute_overall(scores)
    assert abs(overall - expected) < 1e-6


def test_compute_overall_zero_scores():
    """All 0.0 scores yield 0.0 overall."""
    judge = AnswerJudge.__new__(AnswerJudge)
    scores = {
        "faithfulness": 0.0,
        "relevance": 0.0,
        "completeness": 0.0,
        "coherence": 0.0,
        "conciseness": 0.0,
    }
    assert judge._compute_overall(scores) == 0.0


def test_judge_verdict_to_dict():
    """JudgeVerdict.to_dict() returns correct keys and values."""
    verdict = JudgeVerdict(
        faithfulness=0.9,
        relevance=0.8,
        completeness=0.7,
        coherence=0.6,
        conciseness=0.5,
        overall=0.75,
        verdict="pass",
        feedback="Good answer",
        was_regenerated=False,
    )
    d = verdict.to_dict()
    assert d["faithfulness"] == 0.9
    assert d["relevance"] == 0.8
    assert d["completeness"] == 0.7
    assert d["coherence"] == 0.6
    assert d["conciseness"] == 0.5
    assert d["overall"] == 0.75
    assert d["verdict"] == "pass"
    assert d["feedback"] == "Good answer"
    assert d["was_regenerated"] is False
    assert set(d.keys()) == {
        "faithfulness", "relevance", "completeness", "coherence",
        "conciseness", "overall", "verdict", "feedback", "was_regenerated",
    }
