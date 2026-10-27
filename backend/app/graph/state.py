"""
DeviationIQ — LangGraph State Definition

DraftState is the central state object threaded through all graph nodes.
Matches TDD §3 exactly.
"""

from __future__ import annotations

from typing import Annotated, Any, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class DraftState(TypedDict, total=False):
    """
    State dictionary for the LangGraph deviation intake graph.

    - draft_id: UUID string identifying this draft/thread
    - raw_input: the latest user-submitted text or parsed document content
    - input_type: "text" | "file" | "correction"
    - current_fields: dict of field_name → {value, confidence, source_snippet, origin}
    - messages: conversation history (auto-appended via add_messages)
    - pending_assessment: AI-generated RiskAssessment awaiting human confirmation
    - status: draft lifecycle state
    - changed_fields: list of field names changed in the latest operation
    - chat_reply: natural language response to send back to the user
    - router_decision: "extract" | "correct" | "chitchat"
    """
    draft_id: str
    raw_input: str
    input_type: str
    current_fields: dict[str, Any]
    messages: Annotated[list, add_messages]
    pending_assessment: Optional[dict]
    status: str
    changed_fields: list[str]
    chat_reply: str
    router_decision: str
