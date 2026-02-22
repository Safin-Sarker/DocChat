"""Integration tests for EntityExtractor — mock LLM client."""

import json
from unittest.mock import MagicMock

import pytest

from tests.conftest import mock_llm_response
from app.services.entity_extractor import EntityExtractor


@pytest.fixture()
def extractor():
    e = EntityExtractor()
    e.client = MagicMock()
    return e


def test_extract_entities_success(extractor):
    extractor.client.invoke.return_value = mock_llm_response(
        json.dumps({"entities": ["Python", "Docker"]})
    )
    result = extractor.extract_entities("Learn Python and Docker")
    assert result == ["Python", "Docker"]


def test_extract_entities_empty_text(extractor):
    result = extractor.extract_entities("")
    assert result == []
    extractor.client.invoke.assert_not_called()


def test_extract_entities_malformed_json(extractor):
    extractor.client.invoke.return_value = mock_llm_response("not valid json {{{")
    result = extractor.extract_entities("Some text")
    assert result == []


def test_extract_entities_llm_error(extractor):
    extractor.client.invoke.side_effect = RuntimeError("API timeout")
    result = extractor.extract_entities("Some text")
    assert result == []
