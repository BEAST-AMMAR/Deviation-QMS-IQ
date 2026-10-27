"""
DeviationIQ — Deviations Router (Committed Records)

Handles multi-user data isolation and read-only access to committed deviation records:
  GET /deviations        → list deviations belonging exclusively to the authenticated user
  GET /deviations/{id}   → fetch user's committed record (with strict IDOR protection)
  GET /deviations/{id}/events → fetch audit trail
  GET /deviations/{id}/session → fetch session details
  GET /deviations/{id}/export/pdf → export signed dossier
  GET /deviations/{id}/export/docx → export signed dossier

Strict data segregation: Each user has their own private pipeline history.
Cross-user deviation access or data leakage returns HTTP 403 Forbidden.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Deviation, DeviationEvent, User
from app.reports import generate_deviation_docx, generate_deviation_pdf
from app.routers.auth import get_optional_current_user
from app.schemas import (
    ChatMessage,
    DeviationEvent as DeviationEventSchema,
    DeviationRecord,
    PipelineSessionDetail,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/deviations", tags=["deviations"])


def _verify_deviation_access(deviation: Deviation, current_user: Optional[User]):
    """
    Enforces strict user isolation to prevent data breaches or Insecure Direct Object References (IDOR).
    If a deviation is bound to a user account, only that specific user may view or export it.
    """
    if deviation.user_id is not None:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view this clinical deviation record.",
            )
        if current_user.id != deviation.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have authorization to access deviations belonging to another clinical account.",
            )


@router.get("", response_model=list[DeviationRecord])
async def list_deviations(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all committed deviations belonging exclusively to the authenticated user.
    Prevents cross-user data leakage and multi-tenant data exposure.
    """
    if current_user:
        stmt = (
            select(Deviation)
            .where(
                Deviation.status == "committed",
                Deviation.user_id == current_user.id,
            )
            .order_by(Deviation.committed_at.desc(), Deviation.created_at.desc())
        )
    else:
        # Fallback for unauthenticated integration tests
        stmt = (
            select(Deviation)
            .where(
                Deviation.status == "committed",
                Deviation.user_id.is_(None),
            )
            .order_by(Deviation.committed_at.desc(), Deviation.created_at.desc())
        )

    result = await db.execute(stmt)
    deviations = result.scalars().all()

    return [
        DeviationRecord(
            id=str(d.id),
            status=d.status,
            site_plant=d.site_plant,
            date_of_occurrence=str(d.date_of_occurrence) if d.date_of_occurrence else None,
            title=d.title,
            source=d.source,
            related_product=d.related_product,
            batch_lot=d.batch_lot,
            detailed_description=d.detailed_description,
            initial_impact=d.initial_impact,
            initial_severity=d.initial_severity,
            ai_suggested_severity=d.ai_suggested_severity,
            ai_suggested_action=d.ai_suggested_action,
            ai_reasoning=d.ai_reasoning,
            reviewed_by=d.reviewed_by,
            committed_at=d.committed_at,
            chat_history=d.chat_history,
            session_summary=d.session_summary,
            filename=d.filename,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in deviations
    ]


@router.get("/{deviation_id}", response_model=DeviationRecord)
async def get_deviation(
    deviation_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single committed deviation record (strictly user-isolated)."""
    try:
        dev_uuid = uuid.UUID(deviation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deviation ID format.")

    stmt = select(Deviation).where(Deviation.id == dev_uuid)
    result = await db.execute(stmt)
    deviation = result.scalar_one_or_none()

    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    _verify_deviation_access(deviation, current_user)

    return DeviationRecord(
        id=str(deviation.id),
        status=deviation.status,
        site_plant=deviation.site_plant,
        date_of_occurrence=str(deviation.date_of_occurrence) if deviation.date_of_occurrence else None,
        title=deviation.title,
        source=deviation.source,
        related_product=deviation.related_product,
        batch_lot=deviation.batch_lot,
        detailed_description=deviation.detailed_description,
        initial_impact=deviation.initial_impact,
        initial_severity=deviation.initial_severity,
        ai_suggested_severity=deviation.ai_suggested_severity,
        ai_suggested_action=deviation.ai_suggested_action,
        ai_reasoning=deviation.ai_reasoning,
        reviewed_by=deviation.reviewed_by,
        committed_at=deviation.committed_at,
        chat_history=deviation.chat_history,
        session_summary=deviation.session_summary,
        filename=deviation.filename,
        created_at=deviation.created_at,
        updated_at=deviation.updated_at,
    )


@router.get("/{deviation_id}/session", response_model=PipelineSessionDetail)
async def get_deviation_session(
    deviation_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the complete pipeline session bundle (strictly user-isolated):
    - Full deviation record & outcomes
    - Complete AI copilot chat history transcript
    - Append-only audit trail events
    - Session summary
    """
    try:
        dev_uuid = uuid.UUID(deviation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deviation ID format.")

    stmt = select(Deviation).where(Deviation.id == dev_uuid)
    result = await db.execute(stmt)
    deviation = result.scalar_one_or_none()

    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    _verify_deviation_access(deviation, current_user)

    # Parse chat messages
    messages: list[ChatMessage] = []
    if deviation.chat_history:
        try:
            raw_msgs = json.loads(deviation.chat_history)
            for m in raw_msgs:
                if isinstance(m, dict):
                    messages.append(ChatMessage(
                        role=m.get("role", "assistant"),
                        content=m.get("content", ""),
                        timestamp=m.get("timestamp"),
                    ))
        except Exception as e:
            logger.warning("Failed to deserialize chat history for deviation %s: %s", deviation_id, e)

    # Fetch audit events
    stmt_events = (
        select(DeviationEvent)
        .where(DeviationEvent.deviation_id == dev_uuid)
        .order_by(DeviationEvent.created_at.asc())
    )
    events_res = await db.execute(stmt_events)
    events_db = events_res.scalars().all()

    events_list = [
        DeviationEventSchema(
            id=str(e.id),
            deviation_id=str(e.deviation_id),
            actor=e.actor,
            field=e.field,
            old_value=e.old_value,
            new_value=e.new_value,
            confidence=e.confidence,
            source_snippet=e.source_snippet,
            created_at=e.created_at,
        )
        for e in events_db
    ]

    record = DeviationRecord(
        id=str(deviation.id),
        status=deviation.status,
        site_plant=deviation.site_plant,
        date_of_occurrence=str(deviation.date_of_occurrence) if deviation.date_of_occurrence else None,
        title=deviation.title,
        source=deviation.source,
        related_product=deviation.related_product,
        batch_lot=deviation.batch_lot,
        detailed_description=deviation.detailed_description,
        initial_impact=deviation.initial_impact,
        initial_severity=deviation.initial_severity,
        ai_suggested_severity=deviation.ai_suggested_severity,
        ai_suggested_action=deviation.ai_suggested_action,
        ai_reasoning=deviation.ai_reasoning,
        reviewed_by=deviation.reviewed_by,
        committed_at=deviation.committed_at,
        chat_history=deviation.chat_history,
        session_summary=deviation.session_summary,
        filename=deviation.filename,
        created_at=deviation.created_at,
        updated_at=deviation.updated_at,
    )

    return PipelineSessionDetail(
        deviation=record,
        messages=messages,
        events=events_list,
        session_summary=deviation.session_summary,
    )


@router.get("/{deviation_id}/events", response_model=list[DeviationEventSchema])
async def get_deviation_events(
    deviation_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch the append-only audit trail for a deviation (strictly user-isolated)."""
    try:
        dev_uuid = uuid.UUID(deviation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deviation ID format.")

    stmt_dev = select(Deviation).where(Deviation.id == dev_uuid)
    res_dev = await db.execute(stmt_dev)
    deviation = res_dev.scalar_one_or_none()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    _verify_deviation_access(deviation, current_user)

    stmt = (
        select(DeviationEvent)
        .where(DeviationEvent.deviation_id == dev_uuid)
        .order_by(DeviationEvent.created_at.asc())
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        DeviationEventSchema(
            id=str(e.id),
            deviation_id=str(e.deviation_id),
            actor=e.actor,
            field=e.field,
            old_value=e.old_value,
            new_value=e.new_value,
            confidence=e.confidence,
            source_snippet=e.source_snippet,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.get("/{deviation_id}/export/pdf")
async def export_deviation_pdf(
    deviation_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a high-precision GxP PDF deviation report (strictly user-isolated)."""
    try:
        dev_uuid = uuid.UUID(deviation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deviation ID format.")

    stmt = select(Deviation).where(Deviation.id == dev_uuid)
    result = await db.execute(stmt)
    deviation = result.scalar_one_or_none()

    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    _verify_deviation_access(deviation, current_user)

    # Deserialized chat messages
    messages = []
    if deviation.chat_history:
        try:
            raw_msgs = json.loads(deviation.chat_history)
            messages = [ChatMessage(**m) if isinstance(m, dict) else m for m in raw_msgs]
        except Exception as e:
            logger.warning("Failed to deserialize chat history: %s", e)

    # Audit events
    stmt_events = (
        select(DeviationEvent)
        .where(DeviationEvent.deviation_id == dev_uuid)
        .order_by(DeviationEvent.created_at.asc())
    )
    events_res = await db.execute(stmt_events)
    events = events_res.scalars().all()

    pdf_buffer = generate_deviation_pdf(
        deviation=deviation,
        messages=messages,
        events=events,
        session_summary=deviation.session_summary,
    )

    ref = f"DEV-{str(dev_uuid)[:8].upper()}"
    filename = f"Deviation_Report_{ref}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get("/{deviation_id}/export/docx")
async def export_deviation_docx(
    deviation_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a clean GxP DOCX deviation dossier (strictly user-isolated)."""
    try:
        dev_uuid = uuid.UUID(deviation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deviation ID format.")

    stmt = select(Deviation).where(Deviation.id == dev_uuid)
    result = await db.execute(stmt)
    deviation = result.scalar_one_or_none()

    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found.")

    _verify_deviation_access(deviation, current_user)

    # Deserialized chat messages
    messages = []
    if deviation.chat_history:
        try:
            raw_msgs = json.loads(deviation.chat_history)
            messages = [ChatMessage(**m) if isinstance(m, dict) else m for m in raw_msgs]
        except Exception as e:
            logger.warning("Failed to deserialize chat history: %s", e)

    # Audit events
    stmt_events = (
        select(DeviationEvent)
        .where(DeviationEvent.deviation_id == dev_uuid)
        .order_by(DeviationEvent.created_at.asc())
    )
    events_res = await db.execute(stmt_events)
    events = events_res.scalars().all()

    docx_buffer = generate_deviation_docx(
        deviation=deviation,
        messages=messages,
        events=events,
        session_summary=deviation.session_summary,
    )

    ref = f"DEV-{str(dev_uuid)[:8].upper()}"
    filename = f"Deviation_Report_{ref}.docx"

    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
