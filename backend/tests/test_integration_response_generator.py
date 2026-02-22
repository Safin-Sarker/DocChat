"""Integration tests for ResponseGenerator — mock LLM client."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.conftest import mock_llm_response
from app.services.response_generator import ResponseGenerator


@pytest.fixture()
def gen():
    g = ResponseGenerator()
    g.client = MagicMock()
    return g


def test_generate_basic(gen):
    gen.client.invoke.return_value = mock_llm_response("The answer is 42.")
    result = gen.generate("What is the answer?", ["Context chunk 1"])
    assert result == "The answer is 42."
    gen.client.invoke.assert_called_once()


def test_generate_with_feedback(gen):
    gen.client.invoke.return_value = mock_llm_response("Improved answer.")
    result = gen.generate_with_feedback(
        "What is X?", ["ctx1"], feedback="Be more specific"
    )
    assert result == "Improved answer."
    gen.client.invoke.assert_called_once()


def test_build_prompt_includes_contexts(gen):
    prompt = gen._build_prompt("my question", ["alpha", "beta"])
    assert "alpha" in prompt
    assert "beta" in prompt
    assert "my question" in prompt


def test_build_prompt_with_feedback(gen):
    prompt = gen._build_prompt("q", ["ctx"], feedback="Add details")
    assert "Add details" in prompt
    assert "quality review" in prompt.lower() or "feedback" in prompt.lower()


def test_build_messages_with_history(gen):
    history = [
        SimpleNamespace(role="user", content="first question"),
        SimpleNamespace(role="assistant", content="first answer"),
    ]
    messages = gen._build_messages("current prompt", chat_history=history)
    # System + history(user, assistant) + current prompt
    assert len(messages) == 4
    assert messages[0].content  # system message
    assert messages[1].content == "first question"
    assert messages[2].content == "first answer"
    assert messages[3].content == "current prompt"
