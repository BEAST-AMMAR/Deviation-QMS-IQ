"""
DeviationIQ — LangGraph Node Implementations

Each node corresponds to a step in the deviation intake state machine.
See TDD §4 for the full node design table.

Node responsibilities:
  router       → classify intent (extract / correct / chitchat)
  extractor    → extract structured fields from raw text
  risk_assessor → generate severity/impact/reasoning
  patch_node   → apply natural-language corrections to specific fields
  responder    → generate human-readable chat reply
  committer    → (handled at the API layer, not as a graph node here)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import get_settings
from app.graph.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
    PATCH_SYSTEM_PROMPT,
    PATCH_USER_PROMPT,
    RISK_ASSESSMENT_SYSTEM_PROMPT,
    RISK_ASSESSMENT_USER_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    ROUTER_USER_PROMPT,
)
from app.graph.state import DraftState

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_llm_large() -> ChatGroq:
    """Get the large Groq model for extraction and risk assessment."""
    cfg = get_settings()
    return ChatGroq(
        api_key=cfg.groq_api_key,
        model_name=cfg.groq_model_large,
        temperature=0.1,
        max_tokens=4096,
    )


def _get_llm_small() -> ChatGroq:
    """Get the small/fast Groq model for routing classification."""
    cfg = get_settings()
    return ChatGroq(
        api_key=cfg.groq_api_key,
        model_name=cfg.groq_model_small,
        temperature=0.0,
        max_tokens=1024,
    )


def _clean_trailing_commas(s: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", s)


def _parse_json_response(text: str) -> dict:
    """
    Robustly parse JSON from an LLM response using multi-pattern extraction:
    1. Direct json.loads on stripped text
    2. Markdown code fence extraction (```json ... ```)
    3. Outer brace scanning ({ ... }) for conversational preamble/postscript
    4. Trailing comma cleanup recovery
    """
    if not text or not isinstance(text, str):
        return {}

    cleaned = text.strip()

    def _try_load(candidate: str) -> dict | None:
        if not candidate:
            return None
        candidate = candidate.strip()
        try:
            val = json.loads(candidate)
            if isinstance(val, dict):
                return val
        except Exception:
            pass
        try:
            fixed = _clean_trailing_commas(candidate)
            val = json.loads(fixed)
            if isinstance(val, dict):
                return val
        except Exception:
            pass
        return None

    # 1. Direct parse attempt
    res = _try_load(cleaned)
    if res is not None:
        return res

    # 2. Markdown code fences regex extraction
    fence_matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    for match in fence_matches:
        res = _try_load(match)
        if res is not None:
            return res

    # 3. Outer brace scanning (handles conversational preamble / postscript)
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        res = _try_load(cleaned[first_brace : last_brace + 1])
        if res is not None:
            return res

    logger.error("Failed to parse JSON from LLM response: %s", text[:500])
    return {}


# ---------------------------------------------------------------------------
# Router Node
# ---------------------------------------------------------------------------

def router_node(state: DraftState) -> dict:
    """
    Classify user intent: extract, correct, or chitchat.
    Uses the small/fast model — TDD §4 decision for cost/latency.
    """
    # Direct routing for document uploads
    if state.get("input_type") == "file":
        logger.info("File upload detected -> routing directly to extractor")
        return {"router_decision": "extract"}

    llm = _get_llm_small()
    raw_input = state.get("raw_input", "")
    current_fields = state.get("current_fields", {})
    has_fields = "Yes" if any(
        f.get("value") for f in current_fields.values()
        if isinstance(f, dict)
    ) else "No"

    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=ROUTER_USER_PROMPT.format(
            has_fields=has_fields,
            message=raw_input[:500],  # Limit input to router
        )),
    ]

    try:
        response = llm.invoke(messages)
        decision = response.content.strip().lower()
        # Normalize to one of three valid values
        if "extract" in decision:
            decision = "extract"
        elif "correct" in decision:
            decision = "correct"
        else:
            decision = "chitchat"
    except Exception as e:
        logger.error("Router node failed: %s", e)
        # Default to extract for new input, chitchat for errors
        decision = "extract" if not has_fields == "Yes" else "chitchat"

    logger.info("Router decision: %s (has_fields=%s)", decision, has_fields)
    return {"router_decision": decision}


# ---------------------------------------------------------------------------
# Extractor Node
# ---------------------------------------------------------------------------

def extractor_node(state: DraftState) -> dict:
    """
    Extract structured deviation fields from raw text.
    Uses the large model. Returns null for unknown fields — NFR-03.
    """
    llm = _get_llm_large()
    raw_input = state.get("raw_input", "")

    # Guard against exceeding Groq token limits on large PDFs
    if len(raw_input) > 12000:
        logger.info("Truncating large input from %d to 12,000 chars", len(raw_input))
        raw_input = raw_input[:12000] + "\n\n[... document truncated for extraction ...]"

    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=EXTRACTION_USER_PROMPT.format(raw_input=raw_input)),
    ]

    try:
        response = llm.invoke(messages)
        extracted = _parse_json_response(response.content)
    except Exception as e:
        logger.error("Extractor node failed: %s", e)
        return {
            "chat_reply": "I encountered an error processing the text. Please try again.",
            "changed_fields": [],
        }

    if not extracted:
        return {
            "chat_reply": "I couldn't extract any deviation information from the provided text. Please provide a clearer incident report.",
            "changed_fields": [],
        }

    # Merge with existing fields, only overwriting with non-null values
    current_fields = dict(state.get("current_fields", {}))
    changed_fields = []

    for field_name, field_data in extracted.items():
        if isinstance(field_data, dict) and field_data.get("value") is not None:
            old_val = current_fields.get(field_name, {}).get("value") if isinstance(current_fields.get(field_name), dict) else None
            field_data["origin"] = "ai"
            current_fields[field_name] = field_data
            if field_data["value"] != old_val:
                changed_fields.append(field_name)

    # Synthesize title if missing but detailed_description is available
    if not current_fields.get("title", {}).get("value") and current_fields.get("detailed_description", {}).get("value"):
        desc = str(current_fields["detailed_description"]["value"]).strip()
        first_sentence = desc.split(".")[0].strip()
        synth_title = (first_sentence[:80] + "...") if len(first_sentence) > 80 else first_sentence
        if not synth_title:
            synth_title = "Deviation Incident Report"
        current_fields["title"] = {
            "value": synth_title,
            "confidence": "medium",
            "source_snippet": "Synthesized from detailed description",
            "origin": "ai",
        }
        if "title" not in changed_fields:
            changed_fields.append("title")

    # Build a human-readable summary of what was extracted
    populated = [f for f in changed_fields if current_fields.get(f, {}).get("value")]
    missing = [
        f for f in ["site_plant", "date_of_occurrence", "title", "source",
                     "related_product", "batch_lot", "detailed_description"]
        if not current_fields.get(f, {}).get("value")
    ]

    reply_parts = []
    if populated:
        formatted = ', '.join(f.replace('_', ' ') for f in populated)
        reply_parts.append(f"Extracted {len(populated)} field(s): {formatted}.")
    if missing:
        formatted_missing = ', '.join(f.replace('_', ' ') for f in missing)
        reply_parts.append(f"\nCould not find data for: {formatted_missing}.\nYou can provide these manually or leave them empty.")
    
    chat_reply = "\n".join(reply_parts) if reply_parts else "Extraction complete."

    return {
        "current_fields": current_fields,
        "changed_fields": changed_fields,
        "chat_reply": chat_reply,
        "status": "pending_triage",
    }


# ---------------------------------------------------------------------------
# Risk Assessor Node
# ---------------------------------------------------------------------------

def risk_assessor_node(state: DraftState) -> dict:
    """
    Generate severity/impact assessment with reasoning.
    Only runs when required extraction fields are present.
    """
    llm = _get_llm_large()
    current_fields = state.get("current_fields", {})

    def _val(field_name: str) -> str:
        f = current_fields.get(field_name, {})
        return f.get("value", "Not provided") if isinstance(f, dict) else (f or "Not provided")

    messages = [
        SystemMessage(content=RISK_ASSESSMENT_SYSTEM_PROMPT),
        HumanMessage(content=RISK_ASSESSMENT_USER_PROMPT.format(
            site_plant=_val("site_plant"),
            date_of_occurrence=_val("date_of_occurrence"),
            title=_val("title"),
            source=_val("source"),
            related_product=_val("related_product"),
            batch_lot=_val("batch_lot"),
            detailed_description=_val("detailed_description"),
        )),
    ]

    try:
        response = llm.invoke(messages)
        assessment = _parse_json_response(response.content)
    except Exception as e:
        logger.error("Risk assessor node failed: %s", e)
        return {
            "chat_reply": "I encountered an error generating the risk assessment. Please try again.",
        }

    if not assessment or "suggested_severity" not in assessment:
        return {
            "chat_reply": "Could not generate a risk assessment. Please ensure the deviation details are complete.",
        }

    # Normalize severity
    sev = assessment.get("suggested_severity", "Minor")
    if sev not in ("Minor", "Major", "Critical"):
        sev = "Major"
    assessment["suggested_severity"] = sev

    chat_reply = (
        f"Risk Assessment Ready\n\n"
        f"Severity: {assessment['suggested_severity']}\n"
        f"Impact: {assessment.get('suggested_impact', 'See reasoning')}\n\n"
        f"Reasoning:\n{assessment.get('reasoning', 'N/A')}\n\n"
        f"Please review the assessment below and confirm or edit before saving."
    )

    return {
        "pending_assessment": assessment,
        "chat_reply": chat_reply,
        "status": "awaiting_confirmation",
    }


# ---------------------------------------------------------------------------
# Patch Node (Correction)
# ---------------------------------------------------------------------------

def patch_node(state: DraftState) -> dict:
    """
    Apply natural-language corrections to specific fields.
    Only updates fields mentioned in the correction — TDD §4.
    """
    llm = _get_llm_large()
    raw_input = state.get("raw_input", "")
    current_fields = state.get("current_fields", {})

    # Build a simplified view of current fields for the prompt
    simple_fields = {}
    for k, v in current_fields.items():
        if isinstance(v, dict):
            simple_fields[k] = v.get("value", None)
        else:
            simple_fields[k] = v

    messages = [
        SystemMessage(content=PATCH_SYSTEM_PROMPT),
        HumanMessage(content=PATCH_USER_PROMPT.format(
            current_fields_json=json.dumps(simple_fields, indent=2),
            correction_message=raw_input,
        )),
    ]

    try:
        response = llm.invoke(messages)
        patches = _parse_json_response(response.content)
    except Exception as e:
        logger.error("Patch node failed: %s", e)
        return {
            "chat_reply": "I couldn't process that correction. Could you try rephrasing?",
            "changed_fields": [],
        }

    if not patches:
        return {
            "chat_reply": "I couldn't identify which fields to update from your message. "
                         "Please specify the field and the new value.",
            "changed_fields": [],
        }

    # Apply patches
    updated_fields = dict(current_fields)
    changed_fields = []

    for field_name, patch_data in patches.items():
        if field_name in updated_fields or field_name in [
            "site_plant", "date_of_occurrence", "title", "source",
            "related_product", "batch_lot", "detailed_description",
            "initial_impact", "initial_severity",
        ]:
            if isinstance(patch_data, dict) and patch_data.get("value") is not None:
                patch_data["origin"] = "human"
                updated_fields[field_name] = patch_data
                changed_fields.append(field_name)

    # Build reply naming exactly which fields changed (FR-12)
    if changed_fields:
        field_summaries = []
        for f in changed_fields:
            new_val = updated_fields[f].get("value", "")
            field_summaries.append(f"  {f.replace('_', ' ')} → \"{new_val}\"")
        chat_reply = f"Updated {len(changed_fields)} field(s):\n" + "\n".join(field_summaries)
    else:
        chat_reply = "No fields were changed based on your message."

    return {
        "current_fields": updated_fields,
        "changed_fields": changed_fields,
        "chat_reply": chat_reply,
    }


# ---------------------------------------------------------------------------
# Chitchat / Responder Node
# ---------------------------------------------------------------------------

def chitchat_node(state: DraftState) -> dict:
    """
    Handle non-deviation-related messages gracefully (FR-18).
    Does not hallucinate a deviation from empty input.
    """
    return {
        "chat_reply": (
            "I can help you with:\n\n"
            "  Extract — Paste incident report text or upload a document and I'll extract structured deviation fields automatically.\n\n"
            "  Correct — Tell me which field to change and the new value, e.g. 'change the batch number to BT-2025-041'.\n\n"
            "Paste or upload an incident report to get started."
        ),
        "changed_fields": [],
    }
