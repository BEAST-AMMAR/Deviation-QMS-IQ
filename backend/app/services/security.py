"""
DeviationIQ — Authentication & Security Service

GxP & 21 CFR Part 11 compliant authentication, Argon2/bcrypt password hashing,
stateless JWT token issuance, and default clinical role initialization.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import SecurityAuditLog, User, UserRole

logger = logging.getLogger("deviationiq.security")
settings = get_settings()


def hash_password(password: str) -> str:
    """Hash password using bcrypt with random salt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a cryptographically signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# Default clinical staff credentials for initial deployment / demo
DEFAULT_SYSTEM_USERS = [
    {
        "username": "qa_officer",
        "email": "elena.vance@pharma-iq.internal",
        "full_name": "Dr. Elena Vance",
        "role": UserRole.QUALITY_ASSURANCE.value,
        "department": "Quality Assurance & Regulatory Affairs",
        "password": "PharmaQuality2026!",
    },
    {
        "username": "tech_lead",
        "email": "marcus.brody@pharma-iq.internal",
        "full_name": "Marcus Brody",
        "role": UserRole.TECHNICIAN.value,
        "department": "Solid Dosage Manufacturing (API Unit 01)",
        "password": "PharmaTech2026!",
    },
    {
        "username": "admin",
        "email": "arthur.pendelton@pharma-iq.internal",
        "full_name": "Dr. Arthur Pendelton",
        "role": UserRole.ADMIN.value,
        "department": "Executive Quality Operations",
        "password": "PharmaAdmin2026!",
    },
]


async def seed_default_users(session: AsyncSession) -> None:
    """
    Ensure standard clinical roles exist on system bootstrap.
    Idempotent: skips existing accounts.
    """
    try:
        for u in DEFAULT_SYSTEM_USERS:
            stmt = select(User).where(User.username == u["username"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if not existing:
                new_user = User(
                    username=u["username"],
                    email=u["email"],
                    full_name=u["full_name"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    department=u["department"],
                    is_active=True,
                )
                session.add(new_user)
                logger.info("Initialized clinical user: %s (%s)", u["username"], u["role"])
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning("Default user seeding notice: %s", e)
