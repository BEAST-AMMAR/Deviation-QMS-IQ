"""
DeviationIQ — Audit Trail Service

Append-only event logging for ALCOA+ compliance.
Every field mutation (AI or human) is recorded with actor, old value, new value,
confidence, source snippet, and timestamp.

No UPDATE/DELETE operations on deviation_events — SC-06.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeviationEvent

logger = logging.getLogger(__name__)


async def log_field_change(
    db: AsyncSession,
    deviation_id: uuid.UUID,
    actor: str,
    field: str,
    old_value: Optional[str],
    new_value: Optional[str],
    confidence: Optional[str] = None,
    source_snippet: Optional[str] = None,
) -> DeviationEvent:
    """
    Record a single field change in the append-only audit trail.
    
    Called by both AI extraction (actor='ai') and human correction (actor='human').
    """
    event = DeviationEvent(
        deviation_id=deviation_id,
        actor=actor,
        field=field,
        old_value=old_value,
        new_value=new_value,
        confidence=confidence,
        source_snippet=source_snippet,
    )
    db.add(event)
    logger.info(
        "Audit event: %s changed '%s' on %s: '%s' → '%s'",
        actor, field, deviation_id, old_value, new_value,
    )
    return event


async def log_extraction_changes(
    db: AsyncSession,
    deviation_id: uuid.UUID,
    old_fields: dict,
    new_fields: dict,
    actor: str = "ai",
) -> list[str]:
    """
    Compare old and new field dicts and log each change.
    Returns list of field names that changed.
    """
    changed = []
    for field_name, new_data in new_fields.items():
        new_val = new_data.get("value") if isinstance(new_data, dict) else new_data
        old_data = old_fields.get(field_name, {})
        old_val = old_data.get("value") if isinstance(old_data, dict) else old_data

        if new_val is not None and new_val != old_val:
            await log_field_change(
                db=db,
                deviation_id=deviation_id,
                actor=actor,
                field=field_name,
                old_value=str(old_val) if old_val else None,
                new_value=str(new_val),
                confidence=new_data.get("confidence") if isinstance(new_data, dict) else None,
                source_snippet=new_data.get("source_snippet") if isinstance(new_data, dict) else None,
            )
            changed.append(field_name)
    return changed
