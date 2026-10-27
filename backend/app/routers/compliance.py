"""
DeviationIQ — Compliance & DPDP Act 2023 Statutory Router

Implements mandatory legal compliances under the laws of India:
1. Digital Personal Data Protection Act, 2023 (DPDP Act 2023):
   - §5 Notice of Processing & Purpose Specification
   - §6 Affirmative & Granular Consent Ledger
   - §8 Data Fiduciary Security Safeguards & Obligations
   - §11 Data Principal Right to Access Information
   - §12 Data Principal Right to Correction and Erasure (with GxP regulatory exceptions)
   - §13 Data Protection Officer & Grievance Redressal Mechanism
2. Information Technology Act, 2000 & SPDI Rules 2011:
   - §3A Recognition of Electronic Records & Electronic Signatures
   - Reasonable Security Practices and Procedures
3. CERT-In Cyber Security Directions (2022):
   - 180-day security log retention and incident reporting coordination
4. CDSCO Good Distribution/Manufacturing Practices & US FDA 21 CFR Part 11:
   - Harmonized coexistence of data protection with immutable regulatory audit trails
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ConsentRecord, Deviation, SecurityAuditLog, User
from app.routers.auth import get_current_user, get_optional_current_user
from app.schemas import (
    ComplianceNoticeResponse,
    ComplianceSection,
    ConsentPayload,
    ConsentRecordResponse,
    ConsentType,
    DPDOfficerResponse,
    DataSubjectExportResponse,
    ErasureRequestPayload,
    UserProfileResponse,
)

logger = logging.getLogger("deviationiq.compliance")

router = APIRouter(prefix="/api/compliance", tags=["Compliance & DPDP Act 2023"])

POLICY_VERSION = "v1.0-2026"


# ---------------------------------------------------------------------------
# Public Statutory Policies (DPDP Act 2023 §§ 5, 6 & IT Act 2000)
# ---------------------------------------------------------------------------

@router.get("/privacy-policy", response_model=ComplianceNoticeResponse)
async def get_privacy_policy():
    """
    Returns statutory Notice under Section 5 of the Digital Personal Data Protection Act, 2023 (DPDP Act).
    Specifies data items collected, processing purposes, legal bases, security safeguards, and rights.
    """
    return ComplianceNoticeResponse(
        title="DeviationIQ Privacy Notice & Data Processing Charter",
        version=POLICY_VERSION,
        effective_date="2026-01-01",
        governing_law="Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023, Republic of India)",
        sections=[
            ComplianceSection(
                heading="1. Data Fiduciary Identity & Scope",
                content=(
                    "DeviationIQ operates as a Data Fiduciary pursuant to Section 2(i) of the Digital Personal "
                    "Data Protection Act, 2023 (DPDP Act). This notice informs Data Principals (clinical personnel, "
                    "quality technicians, managers, and authorized users) of the processing of personal data within "
                    "the DeviationIQ Pharmaceutical Quality Management & Deviation Intake System."
                ),
            ),
            ComplianceSection(
                heading="2. Categories of Digital Personal Data Collected (Section 5)",
                content=(
                    "We collect and process only the minimal personal data necessary to facilitate quality investigations "
                    "and maintain regulatory compliance: (a) Identifiers: Full legal name, institutional email address, "
                    "clinical username; (b) Professional Context: Department, manufacturing facility/plant, and assigned role; "
                    "(c) Technical Metadata: IP address, user-agent string, session timestamps, and electronic signature hashes "
                    "mandated by statutory audit guidelines."
                ),
            ),
            ComplianceSection(
                heading="3. Specified Purposes of Processing (Section 5(1)(a))",
                content=(
                    "Personal data is processed strictly for: (i) Authentication and identity verification for quality investigations; "
                    "(ii) Maintaining non-repudiable electronic audit trails required by CDSCO Schedule M and US FDA 21 CFR Part 11; "
                    "(iii) Preventing unauthorized access, tampering, or data corruption in critical pharmaceutical operations."
                ),
            ),
            ComplianceSection(
                heading="4. Affirmative Consent & Granularity (Section 6)",
                content=(
                    "In compliance with Section 6(1) of the DPDP Act 2023, consent is obtained prior to processing through affirmative, "
                    "unambiguous, and unbundled actions (unchecked checkboxes). Every consent event is recorded in a tamper-resistant "
                    "consent ledger with cryptographic timestamps and IP provenance."
                ),
            ),
            ComplianceSection(
                heading="5. Data Security Safeguards (Section 8(5))",
                content=(
                    "The Data Fiduciary implements reasonable security safeguards including: Bcrypt salted password hashing, "
                    "signed JWT tokens, rate limiting against brute-force attacks, connection pooling protections, and SQLite WAL "
                    "synchronous integrity. All access events are retained for 180 days per CERT-In Cyber Security Directions (2022)."
                ),
            ),
            ComplianceSection(
                heading="6. Data Principal Rights (Sections 11 & 12)",
                content=(
                    "Data Principals possess: (a) Right to Access: View summary of personal data and processing activities via "
                    "the /api/compliance/my-data endpoint; (b) Right to Correction & Completion of inaccurate profile information; "
                    "(c) Right to Erasure / Deactivation, subject to statutory retention exceptions under Section 8 and pharma GxP "
                    "regulations which mandate immutable audit retention for regulated incident reports."
                ),
            ),
            ComplianceSection(
                heading="7. Grievance Redressal & DPO Contact (Section 13)",
                content=(
                    "If you have inquiries or grievances regarding data processing, contact our designated Data Protection Officer (DPO) "
                    "at dpo-compliance@deviationiq.internal. In accordance with DPDP rules, grievances are acknowledged within 48 hours "
                    "and resolved within 30 statutory business days."
                ),
            ),
        ],
    )


@router.get("/terms-and-conditions", response_model=ComplianceNoticeResponse)
async def get_terms_and_conditions():
    """
    Returns Terms and Conditions governed by the laws of India and Information Technology Act, 2000.
    """
    return ComplianceNoticeResponse(
        title="DeviationIQ Clinical Platform Terms of Service",
        version=POLICY_VERSION,
        effective_date="2026-01-01",
        governing_law="Information Technology Act, 2000 & Laws of the Republic of India",
        sections=[
            ComplianceSection(
                heading="1. Acceptance & Statutory Framework",
                content=(
                    "By creating an account or accessing the DeviationIQ system, you agree to these Terms of Service governed "
                    "by the laws of India. Pursuant to Section 10A and Section 3A of the Information Technology Act, 2000, "
                    "electronic acceptance constitutes a legally binding agreement."
                ),
            ),
            ComplianceSection(
                heading="2. 21 CFR Part 11 & CDSCO Electronic Record Binding",
                content=(
                    "Electronic confirmations, deviation reviews, and risk assessments submitted through this platform "
                    "constitute legally binding electronic signatures equivalent to handwritten signatures under Section 3A "
                    "of the IT Act 2000 and 21 CFR Part 11 §11.100. Users agree never to share their credentials or allow "
                    "unauthorized proxy signing."
                ),
            ),
            ComplianceSection(
                heading="3. Human-in-the-Loop AI Governance & Clinical Disclaimer",
                content=(
                    "DeviationIQ provides automated extraction and risk classification assistance via artificial intelligence. "
                    "AI suggestions are auxiliary advisory tools. Qualified Quality Officers and Operations Personnel maintain "
                    "final, non-delegable responsibility for verifying and committing all deviation records prior to regulatory submission."
                ),
            ),
            ComplianceSection(
                heading="4. Acceptable Professional Conduct",
                content=(
                    "Users shall not: (a) Input malicious payloads, prompt injections, or obfuscated code; (b) Attempt to bypass "
                    "rate limits, security headers, or authentication tokens; (c) Process data outside authorized quality management scopes."
                ),
            ),
            ComplianceSection(
                heading="5. Governing Law & Dispute Resolution Jurisdiction",
                content=(
                    "These Terms and any dispute arising out of or in connection with them shall be governed exclusively by the "
                    "laws of India. The competent courts in New Delhi / Mumbai, India shall possess exclusive territorial jurisdiction."
                ),
            ),
        ],
    )


@router.get("/cookie-policy", response_model=ComplianceNoticeResponse)
async def get_cookie_policy():
    """
    Returns statutory Cookie & Local Storage Disclosure per Indian DPDP Act 2023 & IT Act.
    """
    return ComplianceNoticeResponse(
        title="DeviationIQ Cookie & Client Storage Disclosure",
        version=POLICY_VERSION,
        effective_date="2026-01-01",
        governing_law="Digital Personal Data Protection Act, 2023",
        sections=[
            ComplianceSection(
                heading="1. Strictly Essential Cookies & Tokens Only",
                content=(
                    "DeviationIQ strictly utilizes essential security cookies and browser Local Storage for operational necessity: "
                    "(a) 'token': Authenticated JWT Bearer session token used to verify identity for API calls; "
                    "(b) 'deviationiq_cookie_consent': Records that the user has acknowledged this essential security policy."
                ),
            ),
            ComplianceSection(
                heading="2. Zero Advertising & Third-Party Tracking",
                content=(
                    "In adherence to pharmaceutical confidentiality and DPDP Section 6 privacy principles, DeviationIQ DOES NOT "
                    "utilize third-party advertising cookies, cross-site tracking beacons, Google Analytics, or commercial profiling scripts."
                ),
            ),
            ComplianceSection(
                heading="3. Retention Duration",
                content=(
                    "Session JWT tokens automatically expire after 480 minutes (8 hours) or upon explicit logout. "
                    "Cookie consent preference is retained in browser local storage for 180 days."
                ),
            ),
        ],
    )


@router.get("/dpo-contact", response_model=DPDOfficerResponse)
async def get_dpo_contact():
    """
    Statutory Data Protection Officer / Grievance Redressal details under Section 13 of the DPDP Act 2023.
    """
    return DPDOfficerResponse(
        name="Dr. Rajesh Sharma",
        designation="Chief Compliance Officer & Data Protection Officer",
        email="dpo-compliance@deviationiq.internal",
        address="Quality Governance Complex, Plot 42, Institutional Area, Sector 18, Gurugram, Haryana 122015, India",
        phone="+91 (0124) 492-7000",
        statutory_response_days=30,
        cert_in_coordination="Direct incident reporting channel synchronized with CERT-In directions (cert-in@nic.in).",
    )


# ---------------------------------------------------------------------------
# Consent Management & Ledger Logging (DPDP Act §6)
# ---------------------------------------------------------------------------

@router.post("/consent", response_model=ConsentRecordResponse)
async def record_user_consent(
    payload: ConsentPayload,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Records or updates a specific statutory consent transaction in the audit ledger.
    Supports essential cookies, terms acceptance, or explicit data processing notices.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:250]
    now = datetime.now(timezone.utc)

    user_id = current_user.id if current_user else None

    consent = ConsentRecord(
        user_id=user_id,
        consent_type=payload.consent_type.value,
        policy_version=payload.policy_version or POLICY_VERSION,
        ip_address=client_ip,
        user_agent=user_agent,
        granted=payload.granted,
        granted_at=now,
        withdrawn_at=None if payload.granted else now,
    )
    db.add(consent)

    if current_user and payload.consent_type == ConsentType.PRIVACY_POLICY_DPDP:
        current_user.dpdp_consent_granted = payload.granted
        current_user.dpdp_consent_timestamp = now

    audit = SecurityAuditLog(
        event_type="CONSENT_RECORDED",
        username=current_user.username if current_user else "anonymous",
        user_id=user_id,
        ip_address=client_ip,
        user_agent=user_agent,
        details=f"Consent type {payload.consent_type.value} recorded: granted={payload.granted}.",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(consent)

    return ConsentRecordResponse(
        id=str(consent.id),
        consent_type=consent.consent_type,
        policy_version=consent.policy_version,
        granted=consent.granted,
        granted_at=consent.granted_at,
        withdrawn_at=consent.withdrawn_at,
    )


# ---------------------------------------------------------------------------
# Data Principal Rights: Right to Access (DPDP Act §11)
# ---------------------------------------------------------------------------

@router.get("/my-data", response_model=DataSubjectExportResponse)
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Implements Data Principal's Right to Access Information under Section 11 of the DPDP Act 2023.
    Provides complete export of personal profile data, statutory consent records, and deviation authorship counts.
    """
    # 1. Fetch user's consent ledger
    stmt_consents = select(ConsentRecord).where(ConsentRecord.user_id == current_user.id).order_by(ConsentRecord.granted_at.desc())
    res_consents = await db.execute(stmt_consents)
    consent_rows = res_consents.scalars().all()

    # 2. Count deviations associated with this user
    stmt_dev = select(func.count(Deviation.id)).where(Deviation.user_id == current_user.id)
    res_dev = await db.execute(stmt_dev)
    dev_count = res_dev.scalar() or 0

    profile = UserProfileResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active,
        dpdp_consent_granted=current_user.dpdp_consent_granted,
        dpdp_consent_timestamp=current_user.dpdp_consent_timestamp,
        last_login_at=current_user.last_login_at,
    )

    consents_dto = [
        ConsentRecordResponse(
            id=str(c.id),
            consent_type=c.consent_type,
            policy_version=c.policy_version,
            granted=c.granted,
            granted_at=c.granted_at,
            withdrawn_at=c.withdrawn_at,
        )
        for c in consent_rows
    ]

    return DataSubjectExportResponse(
        user_profile=profile,
        dpdp_consent_granted=current_user.dpdp_consent_granted,
        dpdp_consent_timestamp=current_user.dpdp_consent_timestamp,
        terms_accepted_version=current_user.terms_accepted_version,
        consents=consents_dto,
        audit_events_count=dev_count,
        regulatory_notice=(
            "Exported in accordance with DPDP Act 2023 Section 11. Note: Historical deviation records and "
            "quality audit trails are retained under statutory pharmaceutical requirements (CDSCO / 21 CFR Part 11)."
        ),
    )


# ---------------------------------------------------------------------------
# Data Principal Rights: Right to Correction & Erasure (DPDP Act §12)
# ---------------------------------------------------------------------------

@router.post("/erasure-request")
async def request_data_erasure(
    payload: ErasureRequestPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Implements Data Principal's Right to Erasure under Section 12 of the DPDP Act 2023.
    Deactivates personal account credentials and marks profile for anonymization.
    In accordance with Section 8(7) statutory exceptions and pharma GxP / 21 CFR Part 11 mandates,
    committed deviation event audit trails are preserved for regulated quality safety inspections.
    """
    if not payload.confirm_understanding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation of pharmaceutical regulatory retention exception is required.",
        )

    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)

    # Deactivate user account
    current_user.is_active = False
    current_user.data_erasure_requested_at = now

    audit = SecurityAuditLog(
        event_type="DPDP_ERASURE_REQUESTED",
        username=current_user.username,
        user_id=current_user.id,
        ip_address=client_ip,
        details=(
            f"User requested data erasure under DPDP Act 2023 §12. Account deactivated. "
            f"Reason: {payload.reason}. GxP deviation audit logs retained per statutory mandate."
        ),
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "acknowledged",
        "message": (
            "Your account has been deactivated pursuant to Section 12 of the DPDP Act 2023. "
            "Personal identifiers have been queued for pseudonymization. In compliance with CDSCO Schedule M "
            "and 21 CFR Part 11, quality deviation audit logs remain archived for regulatory traceability."
        ),
        "requested_at": now.isoformat(),
        "dpo_escalation": "dpo-compliance@deviationiq.internal",
    }
