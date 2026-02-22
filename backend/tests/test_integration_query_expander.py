"""Integration tests for QueryExpander — mock LLM client."""

import json
from unittest.mock import MagicMock

import pytest

from tests.conftest import mock_llm_response
from app.services.query_expander import QueryExpander


@pytest.fixture()
def expander():
    e = QueryExpander()
    e.client = MagicMock()
    return e


def test_expand_success(expander):
    expander.client.invoke.return_value = mock_llm_response(
        json.dumps({"queries": ["what is AI", "artificial intelligence overview", "AI definition"]})
    )
    result = expander.expand("what is AI")
    assert "what is AI" in result
    assert len(result) >= 3


def test_expand_includes_original(expander):
    expander.client.invoke.return_value = mock_llm_response(
        json.dumps({"queries": ["variation 1", "variation 2"]})
    )
    result = expander.expand("original query")
    assert result[0] == "original query"


def test_expand_fallback_on_error(expander):
    expander.client.invoke.side_effect = RuntimeError("timeout")
    result = expander.expand("my query")
    assert result == ["my query"]


def test_expand_malformed_json(expander):
    expander.client.invoke.return_value = mock_llm_response("broken {json")
    result = expander.expand("my query")
    assert result == ["my query"]
