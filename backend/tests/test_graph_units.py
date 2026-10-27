"""
DeviationIQ — Unit Tests for LangGraph Node Logic

Tests:
  - JSON parser with code fences, whitespace, and malformed inputs
  - patch_node diff logic and selective field updates
  - Router intent normalization
  - Prompt security structure (Security Plan §3)
"""

from unittest.mock import MagicMock, patch

import pytest

from app.graph.nodes import (
    _parse_json_response,
    patch_node,
    router_node,
)
from app.graph.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    PATCH_SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
)


def test_parse_json_plain():
    raw = '{"site_plant": {"value": "Plant A", "confidence": "high"}}'
    result = _parse_json_response(raw)
    assert result["site_plant"]["value"] == "Plant A"


def test_parse_json_with_code_fences():
    raw = """```json
{
  "batch_lot": {"value": "LOT-1234", "confidence": "high"},
  "title": {"value": "Excursion"}
}
```"""
    result = _parse_json_response(raw)
    assert result["batch_lot"]["value"] == "LOT-1234"
    assert result["title"]["value"] == "Excursion"


def test_parse_json_malformed():
    raw = "Not a JSON document at all"
    result = _parse_json_response(raw)
    assert result == {}


def test_parse_json_with_preamble_and_postscript():
    raw = """Certainly! Here is the extracted JSON for the deviation incident:
```json
{
  "site_plant": {"value": "Dublin Sterile Facility", "confidence": "high"},
  "batch_lot": {"value": "BT-2026-X99", "confidence": "high"}
}
```
Please let me know if you need any additional fields extracted!"""
    result = _parse_json_response(raw)
    assert result["site_plant"]["value"] == "Dublin Sterile Facility"
    assert result["batch_lot"]["value"] == "BT-2026-X99"


def test_parse_json_with_trailing_commas():
    raw = """Here is the result: {
  "title": {"value": "Leakage in Valve V-101", "confidence": "medium",},
  "initial_severity": {"value": "Major",},
}"""
    result = _parse_json_response(raw)
    assert result["title"]["value"] == "Leakage in Valve V-101"
    assert result["initial_severity"]["value"] == "Major"



def test_patch_node_selective_update():
    """Verify patch_node only updates the fields specified by LLM patch diff."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = """```json
{
  "batch_lot": {
    "value": "NEW-LOT-777",
    "confidence": "high",
    "source_snippet": "User stated: actually it was NEW-LOT-777"
  }
}
```"""
    mock_llm.invoke.return_value = mock_response

    state = {
        "raw_input": "Actually the batch number was NEW-LOT-777, not 123",
        "current_fields": {
            "site_plant": {"value": "Site 1", "confidence": "high", "origin": "ai"},
            "batch_lot": {"value": "OLD-123", "confidence": "high", "origin": "ai"},
            "title": {"value": "Temp spike", "confidence": "high", "origin": "ai"},
        },
    }

    with patch("app.graph.nodes._get_llm_large", return_value=mock_llm):
        result = patch_node(state)

    updated_fields = result["current_fields"]
    # Batch was updated
    assert updated_fields["batch_lot"]["value"] == "NEW-LOT-777"
    assert updated_fields["batch_lot"]["origin"] == "human"
    assert "batch_lot" in result["changed_fields"]

    # Other fields remain untouched
    assert updated_fields["site_plant"]["value"] == "Site 1"
    assert updated_fields["title"]["value"] == "Temp spike"
    assert "site_plant" not in result["changed_fields"]


def test_router_node_classification():
    """Verify router normalizes output to extract, correct, or chitchat."""
    mock_llm = MagicMock()

    # Case 1: extract
    mock_llm.invoke.return_value.content = "EXTRACT"
    with patch("app.graph.nodes._get_llm_small", return_value=mock_llm):
        res = router_node({"raw_input": "Reactor R-201 temperature spiked to 78C", "current_fields": {}})
    assert res["router_decision"] == "extract"

    # Case 2: correct
    mock_llm.invoke.return_value.content = "CORRECT"
    with patch("app.graph.nodes._get_llm_small", return_value=mock_llm):
        res = router_node({"raw_input": "Change the date to yesterday", "current_fields": {"site_plant": {"value": "A"}}})
    assert res["router_decision"] == "correct"

    # Case 3: chitchat
    mock_llm.invoke.return_value.content = "CHITCHAT"
    with patch("app.graph.nodes._get_llm_small", return_value=mock_llm):
        res = router_node({"raw_input": "Hello how are you", "current_fields": {}})
    assert res["router_decision"] == "chitchat"


def test_prompts_contain_anti_injection_defenses():
    """Verify system prompts instruct model to treat user text strictly as data."""
    assert "data" in EXTRACTION_SYSTEM_PROMPT.lower()
    assert "never as instructions" in EXTRACTION_SYSTEM_PROMPT.lower() or "do not follow" in EXTRACTION_SYSTEM_PROMPT.lower()
    assert "never follow instructions" in PATCH_SYSTEM_PROMPT.lower() or "data" in PATCH_SYSTEM_PROMPT.lower()
