"""
DeviationIQ — SQLAlchemy ORM Models

Table shapes match 09_Database_Schema_and_ER.md exactly.
Column names are the single source of truth referenced by all layers.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Deviation(Base):
    """
    Primary deviation record — holds current state only.
    History lives in deviation_events (append-only).
    """

    __tablename__ = "deviations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    status = Column(
        String,
        CheckConstraint("status IN ('draft','committed')", name="ck_deviation_status"),
        nullable=False,
        default="draft",
    )

    # --- Deviation Information (FRD §3) ---
    site_plant = Column(Text, nullable=True)
    date_of_occurrence = Column(Date, nullable=True)
    title = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    related_product = Column(Text, nullable=True)
    batch_lot = Column(Text, nullable=True)

    # --- Deviation Details ---
    detailed_description = Column(Text, nullable=True)
    initial_impact = Column(Text, nullable=True)
    initial_severity = Column(Text, nullable=True)

    # --- AI Assessment ---
    ai_suggested_severity = Column(Text, nullable=True)
    ai_suggested_action = Column(Text, nullable=True)
    ai_reasoning = Column(Text, nullable=True)

    # --- Review ---
    reviewed_by = Column(Text, nullable=True)
    committed_at = Column(DateTime(timezone=True), nullable=True)

    # --- Session Transcript & Pipeline History ---
    chat_history = Column(Text, nullable=True)
    session_summary = Column(Text, nullable=True)
    filename = Column(Text, nullable=True)

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


    # --- Relationships ---
    events = relationship("DeviationEvent", back_populates="deviation", cascade="all, delete-orphan")
    extraction_logs = relationship("AIExtractionLog", back_populates="deviation", cascade="all, delete-orphan")


class DeviationEvent(Base):
    """
    Append-only audit trail — every field change (AI or human) is recorded here.
    No UPDATE/DELETE route is exposed at the API layer (SC-06).
    """

    __tablename__ = "deviation_events"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    deviation_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("deviations.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor = Column(
        String,
        CheckConstraint("actor IN ('ai','human')", name="ck_event_actor"),
        nullable=False,
    )
    field = Column(Text, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    confidence = Column(Text, nullable=True)
    source_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # --- Relationships ---
    deviation = relationship("Deviation", back_populates="events")

    __table_args__ = (
        Index("idx_deviation_events_deviation_id", "deviation_id"),
    )


class AIExtractionLog(Base):
    """
    Raw model I/O for debugging and the offline evaluation harness.
    Not shown to end users.
    """

    __tablename__ = "ai_extraction_log"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    deviation_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("deviations.id", ondelete="CASCADE"),
        nullable=True,
    )
    node_name = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    model = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # --- Relationships ---
    deviation = relationship("Deviation", back_populates="extraction_logs")

    __table_args__ = (
        Index("idx_ai_extraction_log_deviation_id", "deviation_id"),
    )
