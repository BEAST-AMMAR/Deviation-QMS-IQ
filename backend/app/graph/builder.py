"""
DeviationIQ — LangGraph Graph Builder

Assembles the StateGraph for the deviation intake workflow:
  router → extractor → risk_assessor (for extract path)
  router → patch_node → (responder logic) (for correct path)
  router → chitchat_node (for chitchat path)

The interrupt() for human confirmation is handled at the API layer
via the graph's pending_assessment state, because LangGraph's interrupt
mechanism works best with synchronous graph invocation patterns.

See SAD §4 and TDD §4 for the full architectural reasoning.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    chitchat_node,
    extractor_node,
    patch_node,
    risk_assessor_node,
    router_node,
)
from app.graph.state import DraftState

logger = logging.getLogger(__name__)


def _route_after_router(state: DraftState) -> str:
    """Conditional edge: route to the correct node based on router decision."""
    decision = state.get("router_decision", "chitchat")
    if decision == "extract":
        return "extractor"
    elif decision == "correct":
        return "patch"
    else:
        return "chitchat"


def _should_assess_risk(state: DraftState) -> str:
    """
    After extraction or correction, check if enough fields are present to run risk assessment.
    Required field for assessment: detailed_description (or title with descriptive content).
    """
    current_fields = state.get("current_fields", {})

    def _has_value(field_name: str) -> bool:
        f = current_fields.get(field_name, {})
        return bool(f.get("value")) if isinstance(f, dict) else bool(f)

    if _has_value("detailed_description") or _has_value("title"):
        # Check if we already have a pending assessment
        if state.get("pending_assessment"):
            return END
        return "risk_assessor"
    return END


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for deviation intake.
    
    Graph topology:
      START → router → [extractor | patch | chitchat]
                         extractor → risk_assessor (if enough fields) → END
                         patch → risk_assessor (if enough fields) → END
                         chitchat → END
    """
    graph = StateGraph(DraftState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("risk_assessor", risk_assessor_node)
    graph.add_node("patch", patch_node)
    graph.add_node("chitchat", chitchat_node)

    # Entry point
    graph.set_entry_point("router")

    # Conditional routing after the router
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "extractor": "extractor",
            "patch": "patch",
            "chitchat": "chitchat",
        },
    )

    # After extraction, conditionally run risk assessment
    graph.add_conditional_edges(
        "extractor",
        _should_assess_risk,
        {
            "risk_assessor": "risk_assessor",
            END: END,
        },
    )

    # After patch/correction, conditionally run risk assessment if ready
    graph.add_conditional_edges(
        "patch",
        _should_assess_risk,
        {
            "risk_assessor": "risk_assessor",
            END: END,
        },
    )

    # Terminal edges
    graph.add_edge("risk_assessor", END)
    graph.add_edge("chitchat", END)

    return graph


# Module-level compiled graph (reusable)
_compiled_graph = None


def get_compiled_graph():
    """Get or compile the graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_graph()
        _compiled_graph = graph.compile()
        logger.info("LangGraph deviation intake graph compiled successfully.")
    return _compiled_graph
