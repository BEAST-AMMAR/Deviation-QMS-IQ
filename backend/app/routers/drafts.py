"""
DeviationIQ â€” Drafts Router

Handles the draft lifecycle:
  POST /drafts             â†’ create new draft
  GET  /drafts/{id}        â†’ fetch current draft state
  POST /drafts/{id}/message â†’ send text/correction to AI graph
  POST /drafts/{id}/upload  â†’ upload document for extraction
  POST /drafts/{id}/confirm â†’ human confirmation of risk assessment
  POST /drafts/{id}/reset   â†’ discard draft

Endpoints match TDD Â§5 exactly.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.graph.builder import get_compiled_graph
from app.models import AIExtractionLog, Deviation, DeviationEvent, User
from app.routers.auth import get_optional_current_user
from app.schemas import (
    ConfirmRequest,
    ConfirmResponse,
    ChatMessage,
    DeviationStatus,
    DirectCommitRequest,
    DraftCreateResponse,
    DraftFieldUpdateRequest,
    DraftFieldsResponse,
    DraftResponse,
    FieldState,
    MessageRequest,
    MessageResponse,
    ResetResponse,
)
from app.services.audit import log_extraction_changes, log_field_change
from app.services.document_parser import parse_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/drafts", tags=["drafts"])

# In-memory draft state store (per-session; in production use Redis or DB)
# Keyed by draft_id â†’ {fields, messages, status, pending_assessment}
_draft_store: dict[str, dict] = {}


def _parse_iso_date(val: Any) -> Optional[date]:
    """Safely parse various date string representations into a date object."""
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        try:
            return date.fromisoformat(val[:10])
        except (ValueError, TypeError):
            pass
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


def _apply_fields_to_deviation(deviation: Deviation, fields_dict: dict):
    """Sync all fields from draft fields dict into the Deviation DB model."""
    for field_name in ["site_plant", "title", "source", "related_product",
                       "batch_lot", "detailed_description", "initial_impact", "initial_severity"]:
        field_data = fields_dict.get(field_name, {})
        value = field_data.get("value") if isinstance(field_data, dict) else field_data
        if value is not None:
            setattr(deviation, field_name, value)

    date_data = fields_dict.get("date_of_occurrence", {})
    date_val = date_data.get("value") if isinstance(date_data, dict) else date_data
    parsed_date = _parse_iso_date(date_val)
    if parsed_date is not None:
        deviation.date_of_occurrence = parsed_date


def _finalize_deviation_session(deviation: Deviation, draft: dict):
    """Save full chat messages transcript, session summary, and filename to deviation."""
    messages_list = draft.get("messages", [])
    deviation.chat_history = json.dumps(messages_list)
    if draft.get("filename"):
        deviation.filename = draft["filename"]
    elif not deviation.filename:
        for m in messages_list:
            c = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
            if "Uploaded file:" in c:
                deviation.filename = c.split("Uploaded file:")[-1].strip()
                break

    summary_parts = []
    if deviation.title:
        summary_parts.append(f"Title: {deviation.title}")
    if deviation.site_plant:
        summary_parts.append(f"Site: {deviation.site_plant}")
    if deviation.date_of_occurrence:
        summary_parts.append(f"Date: {deviation.date_of_occurrence}")
    if deviation.initial_severity:
        summary_parts.append(f"Severity: {deviation.initial_severity}")
    if deviation.initial_impact:
        summary_parts.append(f"Impact: {deviation.initial_impact}")
    if deviation.filename:
        summary_parts.append(f"File: {deviation.filename}")
    if deviation.ai_reasoning:
        summary_parts.append(f"AI Reasoning: {deviation.ai_reasoning[:120]}...")
    summary_parts.append(f"Signed off by {deviation.reviewed_by or 'Quality Officer'}")
    deviation.session_summary = " Â· ".join(summary_parts)


def _hydrate_draft_from_db(draft: dict, deviation: Deviation):
    """Hydrate in-memory draft state from a database Deviation record."""
    if not deviation:
        return
    for field_name in [
        "site_plant", "title", "source", "related_product",
        "batch_lot", "detailed_description", "initial_impact", "initial_severity",
    ]:
        val = getattr(deviation, field_name, None)
        if val is not None and field_name not in draft["fields"]:
            draft["fields"][field_name] = {
                "value": str(val),
                "confidence": "high",
                "source_snippet": "Persisted in record",
                "origin": "human" if deviation.reviewed_by else "ai",
            }

    if deviation.date_of_occurrence and "date_of_occurrence" not in draft["fields"]:
        draft["fields"]["date_of_occurrence"] = {
            "value": str(deviation.date_of_occurrence),
            "confidence": "high",
            "source_snippet": "Persisted in record",
            "origin": "human" if deviation.reviewed_by else "ai",
        }

    if deviation.filename and not draft.get("filename"):
        draft["filename"] = deviation.filename

    if deviation.chat_history and (not draft.get("messages") or len(draft["messages"]) <= 1):
        try:
            stored_msgs = json.loads(deviation.chat_history)
            if isinstance(stored_msgs, list) and stored_msgs:
                draft["messages"] = stored_msgs
        except Exception:
            pass

    if deviation.status == "committed":
        draft["status"] = "committed"
    elif deviation.ai_suggested_severity and not draft.get("pending_assessment"):
        draft["pending_assessment"] = {
            "suggested_severity": deviation.ai_suggested_severity,
            "suggested_impact": deviation.ai_suggested_action or "",
            "reasoning": deviation.ai_reasoning or "",
        }
        draft["status"] = "awaiting_confirmation"


def _get_draft(draft_id: str) -> dict:
    """Get or initialize a draft from the in-memory store."""
    if draft_id not in _draft_store:
        _draft_store[draft_id] = {
            "fields": {},
            "messages": [],
            "status": "pending_triage",
            "pending_assessment": None,
            "deviation_db_id": None,
        }
    return _draft_store[draft_id]


def _fields_to_response(fields: dict) -> DraftFieldsResponse:
    """Convert internal fields dict to the API response model."""
    def _to_field_state(field_data) -> FieldState:
        if isinstance(field_data, dict):
            return FieldState(
                value=field_data.get("value"),
                confidence=field_data.get("confidence"),
                source_snippet=field_data.get("source_snippet"),
                origin=field_data.get("origin", "ai"),
            )
        return FieldState()

    return DraftFieldsResponse(
        site_plant=_to_field_state(fields.get("site_plant", {})),
        date_of_occurrence=_to_field_state(fields.get("date_of_occurrence", {})),
        title=_to_field_state(fields.get("title", {})),
        source=_to_field_state(fields.get("source", {})),
        related_product=_to_field_state(fields.get("related_product", {})),
        batch_lot=_to_field_state(fields.get("batch_lot", {})),
        detailed_description=_to_field_state(fields.get("detailed_description", {})),
        initial_impact=_to_field_state(fields.get("initial_impact", {})),
        initial_severity=_to_field_state(fields.get("initial_severity", {})),
    )


# ---------------------------------------------------------------------------
# POST /drafts â€” Create new draft
# ---------------------------------------------------------------------------

@router.post("", response_model=DraftCreateResponse)
async def create_draft(db: AsyncSession = Depends(get_db)):
    """Create a new deviation draft and its database record."""
    draft_id = str(uuid.uuid4())

    # Create DB record
    deviation = Deviation(id=uuid.UUID(draft_id), status="draft")
    db.add(deviation)
    await db.flush()

    # Initialize in-memory state
    _draft_store[draft_id] = {
        "fields": {},
        "messages": [
            {"role": "system", "content": "Welcome to DeviationIQ. Upload a document or paste report text to begin extraction."}
        ],
        "status": "pending_triage",
        "pending_assessment": None,
        "deviation_db_id": draft_id,
    }

    logger.info("Created draft %s", draft_id)
    return DraftCreateResponse(draft_id=draft_id)


# ---------------------------------------------------------------------------
# GET /drafts/{id} â€” Fetch current draft state
# ---------------------------------------------------------------------------

@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: str, db: AsyncSession = Depends(get_db)):
    """Return the current state of a draft, hydrating from DB if needed."""
    draft = _get_draft(draft_id)

    try:
        dev_uuid = uuid.UUID(draft_id)
        stmt = select(Deviation).where(Deviation.id == dev_uuid)
        result_db = await db.execute(stmt)
        deviation = result_db.scalar_one_or_none()
        if deviation:
            _hydrate_draft_from_db(draft, deviation)
    except (ValueError, TypeError):
        pass

    current_status = DeviationStatus.COMMITTED if draft.get("status") == "committed" else DeviationStatus.DRAFT

    return DraftResponse(
        draft_id=draft_id,
        status=current_status,
        fields=_fields_to_response(draft["fields"]),
        messages=[ChatMessage(**m) if isinstance(m, dict) else m for m in draft["messages"]],
        pending_assessment=draft.get("pending_assessment"),
    )


# ---------------------------------------------------------------------------
# POST /drafts/{id}/message â€” Send text or correction
# ---------------------------------------------------------------------------

@router.post("/{draft_id}/message", response_model=MessageResponse)
async def send_message(
    draft_id: str,
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Process a user message through the LangGraph AI pipeline.
    Routes to extraction, correction, or chitchat based on intent.
    """
    draft = _get_draft(draft_id)
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")

    # Add user message to history
    draft["messages"].append({
        "role": "user",
        "content": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Run the LangGraph pipeline
    graph = get_compiled_graph()
    graph_input = {
        "draft_id": draft_id,
        "raw_input": text,
        "input_type": "text",
        "current_fields": draft["fields"],
        "messages": [],
        "status": draft["status"],
    }

    try:
        result = graph.invoke(graph_input)
    except Exception as e:
        logger.error("Graph invocation failed for draft %s: %s", draft_id, e)
        error_reply = "An error occurred processing your message. Please try again."
        draft["messages"].append({"role": "assistant", "content": error_reply})
        return MessageResponse(
            fields=_fields_to_response(draft["fields"]),
            chat_reply=error_reply,
            changed_fields=[],
            status=DeviationStatus.DRAFT,
        )

    # Update draft state from graph result
    old_fields = dict(draft["fields"])
    if result.get("current_fields"):
        draft["fields"] = result["current_fields"]
    if result.get("status"):
        draft["status"] = result["status"]
    if result.get("pending_assessment"):
        draft["pending_assessment"] = result["pending_assessment"]

    chat_reply = result.get("chat_reply", "Processing complete.")
    changed_fields = result.get("changed_fields", [])

    # Log audit events for changed fields
    if changed_fields:
        try:
            deviation_id = uuid.UUID(draft_id)
            actor = "human" if result.get("router_decision") == "correct" else "ai"
            await log_extraction_changes(
                db=db,
                deviation_id=deviation_id,
                old_fields=old_fields,
                new_fields=draft["fields"],
                actor=actor,
            )
        except Exception as e:
            logger.warning("Audit logging failed for draft %s: %s", draft_id, e)

    # Log AI extraction I/O
    try:
        ai_log = AIExtractionLog(
            deviation_id=uuid.UUID(draft_id),
            node_name=result.get("router_decision", "unknown"),
            prompt=text[:2000],
            raw_response=json.dumps(result.get("current_fields", {}))[:5000],
            model=get_compiled_graph().__class__.__name__,
        )
        db.add(ai_log)
    except Exception as e:
        logger.warning("AI extraction log failed: %s", e)

    # Add assistant reply to history
    draft["messages"].append({
        "role": "assistant",
        "content": chat_reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Update deviation DB record with current field values and chat history
    try:
        stmt = select(Deviation).where(Deviation.id == uuid.UUID(draft_id))
        result_db = await db.execute(stmt)
        deviation = result_db.scalar_one_or_none()
        if deviation:
            _apply_fields_to_deviation(deviation, draft["fields"])
            deviation.chat_history = json.dumps(draft["messages"])
            if draft.get("filename"):
                deviation.filename = draft["filename"]
            await db.flush()
    except Exception as e:
        logger.warning("DB field update failed for draft %s: %s", draft_id, e)

    return MessageResponse(
        fields=_fields_to_response(draft["fields"]),
        chat_reply=chat_reply,
        changed_fields=changed_fields,
        pending_assessment=draft.get("pending_assessment"),
        status=DeviationStatus.DRAFT,
    )


# ---------------------------------------------------------------------------
# POST /drafts/{id}/upload â€” Upload document for extraction
# ---------------------------------------------------------------------------

@router.post("/{draft_id}/upload", response_model=MessageResponse)
async def upload_document(
    draft_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF/DOCX/TXT file, parse it, and run extraction.
    Same extractor prompt as text input â€” single code path (SAD Â§4).
    """
    draft = _get_draft(draft_id)
    draft["filename"] = file.filename or "upload"

    # Read and parse the file
    try:
        file_bytes = await file.read()
        extracted_text = parse_document(
            file_bytes=file_bytes,
            filename=file.filename or "upload",
            content_type=file.content_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("File parsing failed: %s", e)
        raise HTTPException(
            status_code=400,
            detail="Failed to parse the uploaded file. Please ensure it's a valid PDF, DOCX, or TXT file.",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded file appears to be empty or contains no extractable text.",
        )

    # Add a system message about the upload
    draft["messages"].append({
        "role": "user",
        "content": f"Uploaded file: {file.filename}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Run through the same extraction pipeline as text input
    graph = get_compiled_graph()
    graph_input = {
        "draft_id": draft_id,
        "raw_input": extracted_text,
        "input_type": "file",
        "current_fields": draft["fields"],
        "messages": [],
        "status": draft["status"],
    }

    try:
        result = graph.invoke(graph_input)
    except Exception as e:
        logger.error("Graph invocation failed for upload on draft %s: %s", draft_id, e)
        error_reply = "An error occurred processing the uploaded file. Please try again."
        draft["messages"].append({"role": "assistant", "content": error_reply})
        return MessageResponse(
            fields=_fields_to_response(draft["fields"]),
            chat_reply=error_reply,
            changed_fields=[],
            status=DeviationStatus.DRAFT,
        )

    # Update draft state
    old_fields = dict(draft["fields"])
    if result.get("current_fields"):
        draft["fields"] = result["current_fields"]
    if result.get("status"):
        draft["status"] = result["status"]
    if result.get("pending_assessment"):
        draft["pending_assessment"] = result["pending_assessment"]

    chat_reply = result.get("chat_reply", "File processed successfully.")
    changed_fields = result.get("changed_fields", [])

    # Log audit events
    if changed_fields:
        try:
            await log_extraction_changes(
                db=db,
                deviation_id=uuid.UUID(draft_id),
                old_fields=old_fields,
                new_fields=draft["fields"],
                actor="ai",
            )
        except Exception as e:
            logger.warning("Audit logging failed: %s", e)

    draft["messages"].append({
        "role": "assistant",
        "content": chat_reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Update DB record with fields, filename, and chat history
    try:
        stmt = select(Deviation).where(Deviation.id == uuid.UUID(draft_id))
        result_db = await db.execute(stmt)
        deviation = result_db.scalar_one_or_none()
        if deviation:
            _apply_fields_to_deviation(deviation, draft["fields"])
            deviation.filename = draft["filename"]
            deviation.chat_history = json.dumps(draft["messages"])
            await db.flush()
    except Exception as e:
        logger.warning("DB update failed: %s", e)

    return MessageResponse(
        fields=_fields_to_response(draft["fields"]),
        chat_reply=chat_reply,
        changed_fields=changed_fields,
        pending_assessment=draft.get("pending_assessment"),
        status=DeviationStatus.DRAFT,
    )


# ---------------------------------------------------------------------------
# POST /drafts/{id}/confirm â€” Human confirmation of risk assessment
# ---------------------------------------------------------------------------

@router.post("/{draft_id}/confirm", response_model=ConfirmResponse)
async def confirm_assessment(
    draft_id: str,
    request: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Resume past the human confirmation gate.
    Commits the deviation record with the confirmed/edited assessment.
    This is the API surface of the LangGraph interrupt() — SAD §4.
    """
    draft = _get_draft(draft_id)

    # Fetch DB record
    stmt = select(Deviation).where(Deviation.id == uuid.UUID(draft_id))
    result_db = await db.execute(stmt)
    deviation = result_db.scalar_one_or_none()

    if not deviation:
        raise HTTPException(status_code=404, detail="Draft not found.")

    if deviation.status == "committed":
        raise HTTPException(
            status_code=409,
            detail="This deviation is already committed and cannot be modified (SC-07).",
        )

    pending = draft.get("pending_assessment") or {}
    deviation.initial_severity = request.suggested_severity.value
    deviation.initial_impact = request.suggested_impact
    deviation.ai_suggested_severity = pending.get("suggested_severity", "")
    deviation.ai_suggested_action = request.suggested_impact
    deviation.ai_reasoning = request.reasoning
    if current_user:
        deviation.user_id = current_user.id
        deviation.reviewed_by_user_id = current_user.id
        deviation.reviewed_by = f"{current_user.full_name} ({current_user.role})"
    else:
        deviation.reviewed_by = request.reviewed_by
    deviation.status = "committed"
    deviation.committed_at = datetime.now(timezone.utc)

    # Ensure required date and source are present in draft fields for regulatory compliance
    if not draft["fields"].get("date_of_occurrence", {}).get("value"):
        today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        draft["fields"]["date_of_occurrence"] = {
            "value": today_iso,
            "confidence": "high",
            "source_snippet": "Assigned on confirmation",
            "origin": "human",
        }
    if not draft["fields"].get("source", {}).get("value"):
        draft["fields"]["source"] = {
            "value": "Operator Report",
            "confidence": "high",
            "source_snippet": "Defaulted on confirmation",
            "origin": "human",
        }

    # Update all fields from draft (including date_of_occurrence)
    _apply_fields_to_deviation(deviation, draft["fields"])
    _finalize_deviation_session(deviation, draft)


    # Log the confirmation event
    await log_field_change(
        db=db,
        deviation_id=uuid.UUID(draft_id),
        actor="human",
        field="initial_severity",
        old_value=pending.get("suggested_severity"),
        new_value=request.suggested_severity.value,
    )
    await log_field_change(
        db=db,
        deviation_id=uuid.UUID(draft_id),
        actor="human",
        field="status",
        old_value="draft",
        new_value="committed",
    )

    # Update draft store
    draft["status"] = "committed"
    draft["pending_assessment"] = None
    draft["messages"].append({
        "role": "assistant",
        "content": f"Deviation committed successfully. Severity: {request.suggested_severity.value}. Record is now read-only.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    logger.info("Draft %s committed with severity %s", draft_id, request.suggested_severity.value)

    return ConfirmResponse(
        status=DeviationStatus.COMMITTED,
        deviation_id=draft_id,
    )


# ---------------------------------------------------------------------------
# PATCH /drafts/{id}/fields â€” Direct manual field synchronization
# ---------------------------------------------------------------------------

@router.patch("/{draft_id}/fields", response_model=DraftFieldsResponse)
async def update_draft_fields(
    draft_id: str,
    request: DraftFieldUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Direct manual field update from the intake form.
    Persists edits directly into _draft_store and database,
    and logs actor="human" audit trail events (21 CFR Part 11).
    """
    draft = _get_draft(draft_id)
    if draft.get("status") == "committed":
        raise HTTPException(
            status_code=409,
            detail="This deviation is already committed and cannot be modified (SC-07).",
        )

    updates: dict[str, Any] = {}
    if request.fields:
        updates.update(request.fields)
    if request.field_name:
        updates[request.field_name] = request.value

    if not updates:
        raise HTTPException(status_code=400, detail="No field updates provided.")

    old_fields = dict(draft["fields"])
    changed_fields = []

    for f_name, f_val in updates.items():
        existing = draft["fields"].get(f_name, {})
        old_val = existing.get("value") if isinstance(existing, dict) else None
        draft["fields"][f_name] = {
            "value": f_val,
            "confidence": "high",
            "source_snippet": "Manual human entry",
            "origin": request.origin or "human",
        }
        if f_val != old_val:
            changed_fields.append(f_name)

    # Log audit events for changed fields
    if changed_fields:
        try:
            deviation_id = uuid.UUID(draft_id)
            for f_name in changed_fields:
                old_val = old_fields.get(f_name, {}).get("value") if isinstance(old_fields.get(f_name), dict) else None
                new_val = draft["fields"][f_name]["value"]
                await log_field_change(
                    db=db,
                    deviation_id=deviation_id,
                    actor="human",
                    field=f_name,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                )
        except Exception as e:
            logger.warning("Audit logging failed for field update on draft %s: %s", draft_id, e)

    # Update DB record
    try:
        stmt = select(Deviation).where(Deviation.id == uuid.UUID(draft_id))
        result_db = await db.execute(stmt)
        deviation = result_db.scalar_one_or_none()
        if deviation:
            _apply_fields_to_deviation(deviation, draft["fields"])
            await db.flush()
    except Exception as e:
        logger.warning("DB update failed for draft %s: %s", draft_id, e)

    return _fields_to_response(draft["fields"])


# ---------------------------------------------------------------------------
# POST /drafts/{id}/commit â€” Direct Form Submission & Commitment
# ---------------------------------------------------------------------------

@router.post("/{draft_id}/commit", response_model=ConfirmResponse)
async def commit_deviation_direct(
    draft_id: str,
    request: DirectCommitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Direct submission and commitment of deviation form.
    Allows operator to commit the deviation when manually filled or verified,
    enforcing mandatory fields and recording audit trail (21 CFR Part 11).
    """
    draft = _get_draft(draft_id)

    # Fetch DB record
    stmt = select(Deviation).where(Deviation.id == uuid.UUID(draft_id))
    result_db = await db.execute(stmt)
    deviation = result_db.scalar_one_or_none()

    if not deviation:
        raise HTTPException(status_code=404, detail="Draft not found.")

    if deviation.status == "committed":
        raise HTTPException(
            status_code=409,
            detail="This deviation is already committed and cannot be modified (SC-07).",
        )

    # Merge incoming values into draft fields if provided
    request_dict = request.model_dump(exclude_unset=True)
    for field_name in [
        "site_plant", "date_of_occurrence", "title", "source",
        "related_product", "batch_lot", "detailed_description",
        "initial_impact", "initial_severity",
    ]:
        val = request_dict.get(field_name)
        if val is not None:
            draft["fields"][field_name] = {
                "value": val,
                "confidence": "high",
                "source_snippet": "Manual human commitment",
                "origin": "human",
            }

    # Validate required fields
    required_fields = [
        ("site_plant", "Site / Plant"),
        ("date_of_occurrence", "Date of Occurrence"),
        ("title", "Title / Short Description"),
        ("source", "Source"),
        ("detailed_description", "Detailed Description"),
        ("initial_impact", "Initial Impact"),
        ("initial_severity", "Initial Severity"),
    ]
    missing = []
    for f_key, f_label in required_fields:
        f_val = draft["fields"].get(f_key, {})
        val = f_val.get("value") if isinstance(f_val, dict) else f_val
        if not val or not str(val).strip():
            missing.append(f_label)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot commit deviation. Missing required fields: {', '.join(missing)}.",
        )

    # Apply fields to DB record
    _apply_fields_to_deviation(deviation, draft["fields"])
    _finalize_deviation_session(deviation, draft)


    if current_user:
        deviation.user_id = current_user.id
        deviation.reviewed_by_user_id = current_user.id
        deviation.reviewed_by = f"{current_user.full_name} ({current_user.role})"
    else:
        deviation.reviewed_by = request.reviewed_by or "Quality Officer"
    deviation.ai_reasoning = request.reasoning or "Direct human review and commitment."
    deviation.status = "committed"
    deviation.committed_at = datetime.now(timezone.utc)

    # Log audit event
    await log_field_change(
        db=db,
        deviation_id=uuid.UUID(draft_id),
        actor="human",
        field="status",
        old_value="draft",
        new_value="committed",
    )

    # Update draft store
    draft["status"] = "committed"
    draft["pending_assessment"] = None
    draft["messages"].append({
        "role": "assistant",
        "content": "Deviation committed directly and locked into regulatory audit trail. Status: COMMITTED (21 CFR Part 11).",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    logger.info("Draft %s committed directly by %s", draft_id, deviation.reviewed_by)

    return ConfirmResponse(
        status=DeviationStatus.COMMITTED,
        deviation_id=draft_id,
    )



# ---------------------------------------------------------------------------
# POST /drafts/{id}/reset â€” Discard draft
# ---------------------------------------------------------------------------

@router.post("/{draft_id}/reset", response_model=ResetResponse)
async def reset_draft(draft_id: str, db: AsyncSession = Depends(get_db)):
    """Reset a draft, clearing all fields and chat history."""
    if draft_id in _draft_store:
        del _draft_store[draft_id]

    # Delete DB record if it exists and is still a draft
    try:
        stmt = select(Deviation).where(Deviation.id == uuid.UUID(draft_id))
        result_db = await db.execute(stmt)
        deviation = result_db.scalar_one_or_none()
        if deviation and deviation.status == "draft":
            await db.delete(deviation)
    except Exception as e:
        logger.warning("Draft DB cleanup failed: %s", e)

    return ResetResponse(status="reset")
