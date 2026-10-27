"""
DeviationIQ — Pydantic Schemas (Shared Contract)

This is the single source of truth for data shapes across the entire system.
Every field name here matches 04_FRD §3 and 09_Database_Schema exactly.
No layer (frontend, backend, AI) should invent its own naming — NFR-07.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DeviationStatus(str, Enum):
    DRAFT = "draft"
    COMMITTED = "committed"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    MINOR = "Minor"
    MAJOR = "Major"
    CRITICAL = "Critical"


class Actor(str, Enum):
    AI = "ai"
    HUMAN = "human"


class RouterIntent(str, Enum):
    EXTRACT = "extract"
    CORRECT = "correct"
    CHITCHAT = "chitchat"


# ---------------------------------------------------------------------------
# AI Contract — ExtractedField and DeviationExtraction
# ---------------------------------------------------------------------------

class ExtractedField(BaseModel):
    """A single field extracted by the AI, with provenance metadata."""
    value: Optional[str] = None
    confidence: Confidence = Confidence.LOW
    source_snippet: Optional[str] = None


class DeviationExtraction(BaseModel):
    """
    Structured extraction output from the AI extractor node.
    Field names match 04_FRD §3 and 09_Database_Schema exactly.
    """
    site_plant: ExtractedField = Field(default_factory=ExtractedField)
    date_of_occurrence: ExtractedField = Field(default_factory=ExtractedField)
    title: ExtractedField = Field(default_factory=ExtractedField)
    source: ExtractedField = Field(default_factory=ExtractedField)
    related_product: ExtractedField = Field(default_factory=ExtractedField)
    batch_lot: ExtractedField = Field(default_factory=ExtractedField)
    detailed_description: ExtractedField = Field(default_factory=ExtractedField)


class RiskAssessment(BaseModel):
    """AI-suggested severity, impact, and reasoning — requires human confirmation."""
    suggested_severity: Severity
    suggested_impact: str
    reasoning: str


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class DraftCreateResponse(BaseModel):
    draft_id: str


class MessageRequest(BaseModel):
    text: str


class FieldState(BaseModel):
    """Per-field state sent to the frontend, including origin and confidence."""
    value: Optional[str] = None
    confidence: Optional[Confidence] = None
    source_snippet: Optional[str] = None
    origin: Literal["ai", "human"] = "ai"


class DraftFieldsResponse(BaseModel):
    """Current field values and metadata for a draft."""
    site_plant: FieldState = Field(default_factory=FieldState)
    date_of_occurrence: FieldState = Field(default_factory=FieldState)
    title: FieldState = Field(default_factory=FieldState)
    source: FieldState = Field(default_factory=FieldState)
    related_product: FieldState = Field(default_factory=FieldState)
    batch_lot: FieldState = Field(default_factory=FieldState)
    detailed_description: FieldState = Field(default_factory=FieldState)
    initial_impact: FieldState = Field(default_factory=FieldState)
    initial_severity: FieldState = Field(default_factory=FieldState)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None


class DraftResponse(BaseModel):
    draft_id: str
    status: DeviationStatus
    fields: DraftFieldsResponse
    messages: list[ChatMessage] = []
    pending_assessment: Optional[RiskAssessment] = None


class MessageResponse(BaseModel):
    fields: DraftFieldsResponse
    chat_reply: str
    changed_fields: list[str] = []
    pending_assessment: Optional[RiskAssessment] = None
    status: DeviationStatus = DeviationStatus.DRAFT


class ConfirmRequest(BaseModel):
    """Human-reviewed (possibly edited) risk assessment for the confirmation gate."""
    suggested_severity: Severity
    suggested_impact: str
    reasoning: str
    reviewed_by: str = "Quality Officer"


class DraftFieldUpdateRequest(BaseModel):
    """Manual field update from the intake form — supports single field or bulk dict."""
    field_name: Optional[str] = None
    value: Optional[str] = None
    fields: Optional[dict[str, Optional[str]]] = None
    origin: str = "human"


# Alias for backward compatibility
DraftFieldUpdate = DraftFieldUpdateRequest


class DirectCommitRequest(BaseModel):
    """Direct submission/commitment of deviation form fields."""
    site_plant: Optional[str] = None
    date_of_occurrence: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    related_product: Optional[str] = None
    batch_lot: Optional[str] = None
    detailed_description: Optional[str] = None
    initial_impact: Optional[str] = None
    initial_severity: Optional[str] = "Minor"
    reviewed_by: str = "Quality Officer"
    reasoning: Optional[str] = "Human manual verification and direct submission."


class ConfirmResponse(BaseModel):
    status: DeviationStatus
    deviation_id: str


class ResetResponse(BaseModel):
    status: str = "reset"


# ---------------------------------------------------------------------------
# Deviation (committed record) and Audit Event
# ---------------------------------------------------------------------------

class DeviationRecord(BaseModel):
    id: str
    status: DeviationStatus
    site_plant: Optional[str] = None
    date_of_occurrence: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    related_product: Optional[str] = None
    batch_lot: Optional[str] = None
    detailed_description: Optional[str] = None
    initial_impact: Optional[str] = None
    initial_severity: Optional[str] = None
    ai_suggested_severity: Optional[str] = None
    ai_suggested_action: Optional[str] = None
    ai_reasoning: Optional[str] = None
    reviewed_by: Optional[str] = None
    committed_at: Optional[datetime] = None
    chat_history: Optional[str] = None
    session_summary: Optional[str] = None
    filename: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DeviationEvent(BaseModel):
    id: str
    deviation_id: str
    actor: Actor
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    confidence: Optional[str] = None
    source_snippet: Optional[str] = None
    created_at: datetime


class PipelineSessionDetail(BaseModel):
    """Complete session package for reviewing past completed pipeline executions."""
    deviation: DeviationRecord
    messages: list[ChatMessage] = []
    events: list[DeviationEvent] = []
    session_summary: Optional[str] = None


# ---------------------------------------------------------------------------
# Authentication & User Management (21 CFR Part 11 & DPDP Act 2023)
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4)


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool = True
    dpdp_consent_granted: bool = False
    dpdp_consent_timestamp: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=128)
    role: Optional[str] = "technician"
    department: Optional[str] = "Quality & Operations"

    # DPDP Act 2023 §6 & IT Act 2000 Affirmative Consent
    terms_accepted: bool = Field(
        ...,
        description="Affirmative acceptance of Terms & Conditions governed by Indian Law & IT Act 2000"
    )
    privacy_consent: bool = Field(
        ...,
        description="Explicit affirmative consent under Section 6 of Digital Personal Data Protection Act, 2023"
    )
    policy_version: Optional[str] = Field("v1.0-2026", description="Policy version acknowledged")


# ---------------------------------------------------------------------------
# Compliance & DPDP Act 2023 Schemas
# ---------------------------------------------------------------------------

class ConsentType(str, Enum):
    TERMS_AND_CONDITIONS = "terms_and_conditions"
    PRIVACY_POLICY_DPDP = "privacy_policy_dpdp"
    ESSENTIAL_COOKIES = "essential_cookies"
    DATA_PROCESSING = "data_processing"


class ConsentRecordResponse(BaseModel):
    id: str
    consent_type: str
    policy_version: str
    granted: bool
    granted_at: datetime
    withdrawn_at: Optional[datetime] = None


class ConsentPayload(BaseModel):
    consent_type: ConsentType
    policy_version: Optional[str] = "v1.0-2026"
    granted: bool = True


class ErasureRequestPayload(BaseModel):
    reason: Optional[str] = "Exercising Right to Erasure under Section 12 of DPDP Act 2023"
    confirm_understanding: bool = Field(
        ...,
        description="Acknowledges that statutory GxP/CDSCO/21 CFR Part 11 audit trails are exempt from deletion but personal account will be deactivated."
    )


class ComplianceSection(BaseModel):
    heading: str
    content: str


class ComplianceNoticeResponse(BaseModel):
    title: str
    version: str
    effective_date: str
    governing_law: str
    sections: list[ComplianceSection]


class DPDOfficerResponse(BaseModel):
    name: str
    designation: str
    email: str
    address: str
    phone: str
    statutory_response_days: int = 30
    cert_in_coordination: str


class DataSubjectExportResponse(BaseModel):
    user_profile: UserProfileResponse
    dpdp_consent_granted: bool
    dpdp_consent_timestamp: Optional[datetime]
    terms_accepted_version: Optional[str]
    consents: list[ConsentRecordResponse]
    audit_events_count: int
    regulatory_notice: str
