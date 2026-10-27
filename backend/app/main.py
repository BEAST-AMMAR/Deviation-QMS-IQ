"""
DeviationIQ — FastAPI Application Entry Point

Wires together:
  - Enterprise Security Headers middleware
  - CORS middleware
  - Database table creation
  - Draft and Deviation routers
  - Root & Health check endpoints
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import engine
from app.models import Base
from app.routers import drafts, deviations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

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
    """Startup: create tables if they don't exist. Shutdown: dispose engine."""
    logger.info("Starting DeviationIQ backend...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created via primary engine.")
    except Exception as e:
        logger.warning(
            "Primary database connection failed: %s. Falling back to local SQLite engine...", e
        )
        from app.database import init_sqlite_fallback
        await init_sqlite_fallback()

    yield
    from app.database import engine as current_engine
    await current_engine.dispose()
    logger.info("DeviationIQ backend shut down.")


app = FastAPI(
    title="DeviationIQ — AI-Powered Deviation Intake Module",
    description="API for the AI-assisted pharmaceutical deviation logging system compliant with 21 CFR Part 11 and ICH Q9/Q10.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Security Headers ---
app.add_middleware(SecurityHeadersMiddleware)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(drafts.router)
app.include_router(deviations.router)


# --- Root & Discovery Endpoint ---
@app.get("/", tags=["system"])
async def root():
    return {
        "service": "DeviationIQ — AI-Powered Deviation Intake Module",
        "compliance": "FDA 21 CFR Part 11 / ICH Q9 & Q10 / GAMP 5",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "drafts": "/api/drafts",
            "deviations": "/api/deviations",
        },
    }


# --- Health Check Endpoints ---
@app.get("/api/health", tags=["system"])
@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "service": "DeviationIQ Deviation Intake Module",
        "version": "1.0.0",
        "compliance": "21 CFR Part 11 Sealed",
    }
