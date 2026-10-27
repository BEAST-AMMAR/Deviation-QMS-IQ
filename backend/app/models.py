"""
DeviationIQ — SQLAlchemy ORM Models

Table shapes match 09_Database_Schema_and_ER.md and 21 CFR Part 11 requirements.
Includes User, Deviation, DeviationEvent (ALCOA+ audit ledger), and SecurityAuditLog.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    QUALITY_ASSURANCE = "quality_assurance"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class User(Base):
    """
    Authenticated pharmaceutical personnel subject to 21 CFR Part 11 electronic signature controls.
    """

    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(
        String(32),
        CheckConstraint(
            "role IN ('admin','quality_assurance','technician','viewer')",
            name="ck_user_role",
        ),
        nullable=False,
        default="technician",
    )
    department = Column(String(64), nullable=True, default="Quality & Compliance")
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # DPDP Act 2023 & IT Act 2000 Statutory Consent Audit
    dpdp_consent_granted = Column(Boolean, default=False, nullable=False)
    dpdp_consent_timestamp = Column(DateTime(timezone=True), nullable=True)
    terms_accepted_version = Column(String(16), nullable=True, default="v1.0-2026")
    data_erasure_requested_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    deviations = relationship("Deviation", back_populates="creator", foreign_keys="Deviation.user_id")
    consent_records = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")


class ConsentRecord(Base):
    """
    Statutory consent ledger per Section 6 of Digital Personal Data Protection Act, 2023 (DPDP Act).
    Audit trail for terms acceptance, privacy policy consent, and cookie disclosures.
    """

    __tablename__ = "consent_records"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    consent_type = Column(String(64), nullable=False, index=True)
    policy_version = Column(String(16), nullable=False, default="v1.0-2026")
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    granted = Column(Boolean, nullable=False, default=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="consent_records")

    __table_args__ = (
        Index("idx_consent_records_user_id", "user_id"),
        Index("idx_consent_records_type", "consent_type"),
    )


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

    # --- Attribution & Ownership (21 CFR Part 11) ---
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

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
    creator = relationship("User", foreign_keys=[user_id], back_populates="deviations")
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
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
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


class SecurityAuditLog(Base):
    """
    Server security & access audit trail per 21 CFR Part 11 §11.10(e).
    Records authentication events, account lockouts, rate limit violations, and security changes.
    """

    __tablename__ = "security_audit_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=_new_uuid)
    event_type = Column(String(64), nullable=False, index=True)
    username = Column(String(64), nullable=True, index=True)
    user_id = Column(Uuid(as_uuid=True), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("idx_security_audit_event_type", "event_type"),
        Index("idx_security_audit_created_at", "created_at"),
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
