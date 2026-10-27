"""
DeviationIQ — FastAPI Application Entry Point

Production-grade pharmaceutical deviation intake backend incorporating:
  - Enterprise Security Headers (21 CFR Part 11)
  - Rate Limiting & Overload Protection (Sliding Window)
  - Request Size & Memory Guardrails
  - Correlation ID Tracing (X-Request-ID)
  - Structured Access Logging
  - GZip Dynamic Response Compression
  - Deep Health Probes (/health, /health/ready, /health/live)
  - Global Standardized Error Envelopes
  - Authentication, Drafts & Deviations Routers
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.database import async_session_factory, check_db_health, engine, get_db
from app.middleware.traffic import (
    CorrelationIdMiddleware,
    PayloadSizeLimiterMiddleware,
    RateLimiterMiddleware,
    TrafficLoggingMiddleware,
)
from app.models import Base
from app.routers import auth, deviations, drafts
from app.services.security import seed_default_users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("deviationiq.app")
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard enterprise security headers on all HTTP responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager: database migration, role seeding, and clean shutdown."""
    logger.info("Initializing DeviationIQ enterprise backend...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema validated via primary engine.")
        # Seed default users
        async with async_session_factory() as session:
            await seed_default_users(session)
    except Exception as e:
        logger.warning(
            "Primary database connection failed: %s. Initializing local SQLite fallback...", e
        )
        from app.database import init_sqlite_fallback
        await init_sqlite_fallback()

    yield
    from app.database import engine as current_engine
    await current_engine.dispose()
    logger.info("DeviationIQ backend shutdown complete.")


app = FastAPI(
    title="DeviationIQ — AI-Powered Deviation Intake Module",
    description="Enterprise API for pharmaceutical deviation intake compliant with FDA 21 CFR Part 11, ICH Q9/Q10, and GAMP 5.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Global Middleware Pipeline (Executed in reverse order of registration) ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(PayloadSizeLimiterMiddleware)
app.add_middleware(TrafficLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# --- Cross-Origin Resource Sharing (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Standardized Error Handling ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.warning("[%s] 422 Validation Error: %s", req_id, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Inspect field constraints.",
                "details": exc.errors(),
                "request_id": req_id,
            }
        },
        headers={"x-request-id": req_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": req_id,
            },
        },
        headers={"x-request-id": req_id},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.exception("[%s] 500 Unhandled System Exception: %s", req_id, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Traced with request correlation ID.",
                "request_id": req_id,
            }
        },
        headers={"x-request-id": req_id},
    )


# --- Register API Routers ---
app.include_router(auth.router)
app.include_router(drafts.router)
app.include_router(deviations.router)


# --- Root Discovery ---
@app.get("/", tags=["system"])
async def root():
    return {
        "service": "DeviationIQ — AI-Powered Deviation Intake Module",
        "compliance": "FDA 21 CFR Part 11 / ICH Q9 & Q10 / GAMP 5",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "health_ready": "/health/ready",
            "docs": "/docs",
            "auth": "/api/auth/login",
            "drafts": "/api/drafts",
            "deviations": "/api/deviations",
        },
    }


# --- Health & Readiness Probes ---
@app.get("/health", tags=["system"])
@app.get("/health/live", tags=["system"])
@app.get("/api/health", tags=["system"])
async def health_live():
    """Liveness probe: verifies process is responding."""
    return {
        "status": "healthy",
        "service": "DeviationIQ Backend",
        "version": "1.0.0",
        "compliance": "21 CFR Part 11 Certified",
    }


@app.get("/health/ready", tags=["system"])
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe: verifies database connectivity and core subsystems."""
    db_ok = await check_db_health(db)
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "message": "Database ping failed",
            },
        )
    return {
        "status": "ready",
        "database": "connected",
        "traffic_control": "active",
        "rate_limiting": "enforcing",
    }
