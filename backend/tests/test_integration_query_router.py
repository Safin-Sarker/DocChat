"""Integration tests for QueryRouter — mock LLM client."""

import json
from unittest.mock import MagicMock

import pytest

from tests.conftest import mock_llm_response
from app.services.query_router import QueryRouter


@pytest.fixture()
def router():
    r = QueryRouter()
    r.client = MagicMock()
    return r


def test_classify_greeting(router):
    router.client.invoke.return_value = mock_llm_response(json.dumps({"intent": "greeting"}))
    assert router.classify("Hi") == "greeting"
    router.client.invoke.assert_called_once()


def test_classify_document_query(router):
    router.client.invoke.return_value = mock_llm_response(json.dumps({"intent": "document_query"}))
    assert router.classify("What are the side effects?") == "document_query"


def test_classify_summary(router):
    router.client.invoke.return_value = mock_llm_response(json.dumps({"intent": "summary"}))
    assert router.classify("Summarize the document") == "summary"


def test_classify_fallback_on_error(router):
    router.client.invoke.side_effect = RuntimeError("LLM unavailable")
    assert router.classify("anything") == "document_query"


def test_generate_casual_response(router):
    router.client.invoke.return_value = mock_llm_response("Hello! How can I help you today?")
    result = router.generate_casual_response("Hi there")
    assert result == "Hello! How can I help you today?"
    router.client.invoke.assert_called_once()
