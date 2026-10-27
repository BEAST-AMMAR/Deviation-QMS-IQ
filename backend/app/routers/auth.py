"""
DeviationIQ — Authentication & User Management Endpoints

Complies with 21 CFR Part 11 electronic authentication standards:
- Secure password hashing (bcrypt)
- Account lockout policy (5 failed attempts -> 15 min lock)
- JWT bearer tokens
- Immutable security audit logs
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import ConsentRecord, SecurityAuditLog, User, UserRole
from app.schemas import CreateUserRequest, LoginRequest, TokenResponse, UserProfileResponse
from app.services.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger("deviationiq.auth")
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Management"])


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency validating Bearer JWT tokens.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(payload["sub"]))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token claims.",
        )

    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated or no longer exists.",
        )

    return user


async def get_optional_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication dependency for backward compatibility.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_current_user(authorization, db)
    except Exception:
        return None


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate clinical personnel and issue a signed JWT access token.
    Enforces brute-force lockout defense and 21 CFR Part 11 audit logging.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    stmt = select(User).where(User.username == req.username.strip().lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    # 1. User existence & lockout check
    if not user:
        # Audit failed login attempt
        audit = SecurityAuditLog(
            event_type="LOGIN_FAILED_USER_NOT_FOUND",
            username=req.username,
            ip_address=client_ip,
            user_agent=user_agent,
            details="Login attempt with unregistered username.",
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid clinical username or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended by Quality Administration.",
        )

    if user.locked_until and user.locked_until > now:
        remaining_minutes = max(1, int((user.locked_until - now).total_seconds() / 60))
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to multiple failed login attempts. Retry in {remaining_minutes} minutes.",
        )

    # 2. Password verification
    if not verify_password(req.password, user.hashed_password):
        user.failed_login_attempts += 1
        lock_message = ""
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            lock_message = " Account locked for 15 minutes."

        audit = SecurityAuditLog(
            event_type="LOGIN_FAILED_BAD_PASSWORD",
            username=user.username,
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details=f"Incorrect password attempt #{user.failed_login_attempts}.{lock_message}",
        )
        db.add(audit)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid clinical username or password.{lock_message}",
        )

    # 3. Successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    audit = SecurityAuditLog(
        event_type="LOGIN_SUCCESS",
        username=user.username,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details=f"Authenticated as role {user.role}.",
    )
    db.add(audit)
    await db.commit()

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "department": user.department,
    }
    token = create_access_token(token_data)

    user_profile = UserProfileResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        dpdp_consent_granted=user.dpdp_consent_granted,
        dpdp_consent_timestamp=user.dpdp_consent_timestamp,
        last_login_at=user.last_login_at,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user_profile,
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns profile information of currently authenticated user.
    """
    return UserProfileResponse(
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


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Log clinical user sign-out event per audit regulations.
    """
    client_ip = request.client.host if request.client else "unknown"
    audit = SecurityAuditLog(
        event_type="LOGOUT",
        username=current_user.username,
        user_id=current_user.id,
        ip_address=client_ip,
        details="User voluntarily terminated clinical session.",
    )
    db.add(audit)
    await db.commit()
    return {"message": "Session terminated successfully."}


@router.post("/register", response_model=TokenResponse)
async def register_user(
    req: CreateUserRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Public self-service user registration with DPDP Act 2023 & IT Act 2000 consent enforcement.
    Requires affirmative, unbundled consent before account provisioning and logs a tamper-resistant consent ledger.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:250]

    # Statutory Affirmative Consent Verification (DPDP Act 2023 §6 & IT Act 2000 §3A)
    if not req.terms_accepted or not req.privacy_consent:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Under Section 6 of the Digital Personal Data Protection Act, 2023 (DPDP Act) and the Information Technology Act, 2000, affirmative consent to the Privacy Policy and Terms of Service is mandatory to register an account.",
        )

    clean_username = req.username.strip().lower()
    clean_email = req.email.strip().lower()

    # Validate role against permitted roles
    valid_roles = [r.value for r in UserRole]
    chosen_role = req.role if req.role in valid_roles else UserRole.TECHNICIAN.value

    # Check collision
    stmt = select(User).where((User.username == clean_username) | (User.email == clean_email))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this username or email address is already registered.",
        )

    now = datetime.now(timezone.utc)
    policy_ver = req.policy_version or "v1.0-2026"

    new_user = User(
        username=clean_username,
        email=clean_email,
        full_name=req.full_name.strip(),
        hashed_password=hash_password(req.password),
        role=chosen_role,
        department=req.department.strip() if req.department else "API Manufacturing Unit 01",
        is_active=True,
        dpdp_consent_granted=True,
        dpdp_consent_timestamp=now,
        terms_accepted_version=policy_ver,
        last_login_at=now,
    )
    db.add(new_user)
    await db.flush()

    # Record tamper-resistant consent ledger entries per DPDP Act 2023 §6
    consent_terms = ConsentRecord(
        user_id=new_user.id,
        consent_type="terms_and_conditions",
        policy_version=policy_ver,
        ip_address=client_ip,
        user_agent=user_agent,
        granted=True,
        granted_at=now,
    )
    consent_privacy = ConsentRecord(
        user_id=new_user.id,
        consent_type="privacy_policy_dpdp",
        policy_version=policy_ver,
        ip_address=client_ip,
        user_agent=user_agent,
        granted=True,
        granted_at=now,
    )
    db.add(consent_terms)
    db.add(consent_privacy)

    audit = SecurityAuditLog(
        event_type="USER_REGISTERED_WITH_DPDP_CONSENT",
        username=clean_username,
        user_id=new_user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        details=f"Self-registered account created with role {chosen_role}. DPDP Act 2023 §6 consent logged under version {policy_ver}.",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(new_user)

    token_data = {
        "sub": str(new_user.id),
        "username": new_user.username,
        "role": new_user.role,
        "full_name": new_user.full_name,
        "department": new_user.department,
    }
    token = create_access_token(token_data)

    user_profile = UserProfileResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        department=new_user.department,
        is_active=new_user.is_active,
        dpdp_consent_granted=new_user.dpdp_consent_granted,
        dpdp_consent_timestamp=new_user.dpdp_consent_timestamp,
        last_login_at=new_user.last_login_at,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user_profile,
    )


@router.get("/audit", dependencies=[Depends(get_current_user)])
async def get_security_audit_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve security audit trail for 21 CFR Part 11 regulatory inspections.
    """
    stmt = select(SecurityAuditLog).order_by(desc(SecurityAuditLog.created_at)).limit(min(limit, 200))
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "event_type": l.event_type,
            "username": l.username,
            "ip_address": l.ip_address,
            "details": l.details,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
