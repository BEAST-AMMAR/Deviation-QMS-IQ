"""
DeviationIQ — Offline AI Evaluation Harness

Runs extraction and risk assessment against the synthetic fixtures,
comparing field-by-field results to hand-labeled expected values.

Usage:
    cd backend
    python -m app.eval.run_eval

This runs BEFORE frontend work begins (Roadmap Phase 2).
"""

from __future__ import annotations

import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
# Load .env from project root or backend
env_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(env_root)

from app.eval.fixtures import FIXTURES
from app.graph.builder import get_compiled_graph


def run_evaluation():
    """Run the evaluation harness against all fixtures."""
    graph = get_compiled_graph()
    results = []
    total_fields = 0
    correct_fields = 0
    null_correct = 0
    null_total = 0

    print("\n" + "=" * 70)
    print("  DeviationIQ — AI Extraction Evaluation Harness")
    print("=" * 70)

    for fixture in FIXTURES:
        fid = fixture["id"]
        print(f"\n{'─' * 60}")
        print(f"  Fixture: {fid}")
        print(f"  Description: {fixture['description']}")
        print(f"{'─' * 60}")

        # Skip correction fixture (different evaluation path)
        if fixture.get("expected_router_decision") == "correct":
            print("  [SKIP] Correction fixture — evaluated separately")
            continue

        # Run the graph
        graph_input = {
            "draft_id": fid,
            "raw_input": fixture["input_text"],
            "input_type": "text",
            "current_fields": {},
            "messages": [],
            "status": "pending_triage",
        }

        try:
            result = graph.invoke(graph_input)
        except Exception as e:
            print(f"  ❌ Graph invocation FAILED: {e}")
            results.append({"id": fid, "status": "error", "error": str(e)})
            continue

        extracted_fields = result.get("current_fields", {})
        expected_fields = fixture.get("expected_fields", {})

        fixture_result = {"id": fid, "status": "ok", "field_results": {}}

        for field_name, expected_val in expected_fields.items():
            total_fields += 1
            actual_data = extracted_fields.get(field_name, {})
            actual_val = actual_data.get("value") if isinstance(actual_data, dict) else actual_data

            if expected_val is None:
                null_total += 1
                if actual_val is None or actual_val == "" or actual_val == "null":
                    null_correct += 1
                    correct_fields += 1
                    status = "✅ NULL (correct)"
                else:
                    status = f"❌ HALLUCINATED: got '{actual_val}' (expected null)"
            else:
                # Fuzzy match: check substring in either direction or word overlap >= 50%
                exp_clean = expected_val.lower().strip()
                act_clean = str(actual_val).lower().strip() if actual_val else ""
                
                exp_words = set(w for w in exp_clean.replace(",", " ").replace(".", " ").replace("—", " ").split() if len(w) > 2)
                act_words = set(w for w in act_clean.replace(",", " ").replace(".", " ").replace("—", " ").split() if len(w) > 2)
                overlap = len(exp_words & act_words) / max(len(exp_words), 1) if exp_words else 0

                if act_clean and (exp_clean in act_clean or act_clean in exp_clean or overlap >= 0.4):
                    correct_fields += 1
                    status = "✅ MATCH"
                elif act_clean:
                    status = f"⚠️ PARTIAL: got '{actual_val[:60]}...'"
                else:
                    status = "❌ MISSING"

            confidence = actual_data.get("confidence", "?") if isinstance(actual_data, dict) else "?"
            print(f"  {field_name:25s} {status}  [confidence: {confidence}]")
            fixture_result["field_results"][field_name] = status

        # Check risk assessment if pending
        pending = result.get("pending_assessment")
        expected_sev = fixture.get("expected_severity")
        if pending and expected_sev:
            actual_sev = pending.get("suggested_severity", "?")
            if actual_sev == expected_sev:
                print(f"  {'severity':25s} ✅ {actual_sev}")
            else:
                print(f"  {'severity':25s} ⚠️ got {actual_sev}, expected {expected_sev}")

        results.append(fixture_result)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total fields evaluated:  {total_fields}")
    print(f"  Correct (fuzzy match):   {correct_fields}/{total_fields} ({100*correct_fields/max(total_fields,1):.0f}%)")
    print(f"  Null-correctness:        {null_correct}/{null_total} (hallucination test)")
    print(f"{'=' * 70}\n")

    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
    run_evaluation()
