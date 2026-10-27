"""
DeviationIQ — Traffic, Overload Protection & Correlation Middleware

Features:
- Correlation ID Injection (X-Request-ID)
- Request Payload Size Limiting (Protection against memory exhaustion)
- Token Bucket / Sliding Window Rate Limiting (Per-route & Per-IP)
- High-Performance Request Timing & Structured Access Logging
- Asynchronous Concurrency Semaphore for LLM Gate
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

logger = logging.getLogger("deviationiq.traffic")
settings = get_settings()

# Global LLM Concurrency Semaphore (thread-safe for LangGraph nodes)
llm_concurrency_gate = threading.Semaphore(settings.llm_concurrency_limit)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Ensures every HTTP transaction bears an immutable, traceable correlation ID.
    Propagates X-Request-ID in response headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("x-request-id")
        if not req_id:
            req_id = f"req-{uuid.uuid4().hex[:12]}"

        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["x-request-id"] = req_id
        return response


class PayloadSizeLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rejects oversized payloads before body buffering to prevent Denial-of-Service / OOM.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > settings.max_request_body_bytes:
                    limit_mb = settings.max_request_body_bytes // (1024 * 1024)
                    req_id = getattr(request.state, "request_id", "unknown")
                    logger.warning(
                        "[%s] 413 Payload Too Large: %d bytes (limit: %d MB)",
                        req_id,
                        length_int,
                        limit_mb,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Payload size exceeds the {limit_mb} MB threshold.",
                                "request_id": req_id,
                            }
                        },
                        headers={"x-request-id": req_id},
                    )
            except ValueError:
                pass
        return await call_next(request)


class SlidingWindowRateLimiter:
    """
    In-memory sliding window rate limiter tracking request timestamps per client/route.
    """

    def __init__(self):
        # key: (client_ip, bucket_name) -> list of unix timestamps
        self._history: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()

    async def check(self, key: Tuple[str, str], limit: int, window_seconds: int = 60) -> Tuple[bool, int, int]:
        """
        Returns (is_allowed, remaining_requests, retry_after_seconds).
        """
        now = time.time()
        async with self._lock:
            # Periodic cleanup of records older than 5 minutes
            if now - self._last_cleanup > 60:
                expired = now - 300
                keys_to_delete = []
                for k, timestamps in self._history.items():
                    self._history[k] = [t for t in timestamps if t > expired]
                    if not self._history[k]:
                        keys_to_delete.append(k)
                for k in keys_to_delete:
                    del self._history[k]
                self._last_cleanup = now

            timestamps = self._history[key]
            # Discard timestamps outside current window
            window_cutoff = now - window_seconds
            valid_timestamps = [t for t in timestamps if t > window_cutoff]
            self._history[key] = valid_timestamps

            count = len(valid_timestamps)
            if count >= limit:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest)))
                return False, 0, retry_after

            # Allow request and record timestamp
            valid_timestamps.append(now)
            remaining = limit - count - 1
            return True, remaining, 0


rate_limiter = SlidingWindowRateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Enforces route-specific traffic ceilings with RFC standard 429 & Retry-After headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Determine route-specific rate limit tier
        if path.startswith("/api/auth"):
            bucket = "auth"
            limit = settings.rate_limit_auth_per_minute
        elif path.startswith("/api/drafts"):
            bucket = "drafts"
            limit = settings.rate_limit_ai_per_minute
        elif path.startswith("/api"):
            bucket = "api"
            limit = settings.rate_limit_per_minute
        else:
            # Non-API / health checks are unmetered
            return await call_next(request)

        allowed, remaining, retry_after = await rate_limiter.check((client_ip, bucket), limit)
        req_id = getattr(request.state, "request_id", "unknown")

        if not allowed:
            logger.warning(
                "[%s] Rate limit exceeded for IP %s on tier '%s' (limit: %d/min)",
                req_id,
                client_ip,
                bucket,
                limit,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "TOO_MANY_REQUESTS",
                        "message": f"Rate limit exceeded. Tier limit is {limit} requests per minute.",
                        "request_id": req_id,
                        "retry_after_seconds": retry_after,
                    }
                },
                headers={
                    "x-request-id": req_id,
                    "retry-after": str(retry_after),
                    "x-ratelimit-limit": str(limit),
                    "x-ratelimit-remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["x-ratelimit-limit"] = str(limit)
        response.headers["x-ratelimit-remaining"] = str(remaining)
        return response


class TrafficLoggingMiddleware(BaseHTTPMiddleware):
    """
    Emits structured, high-precision telemetry for every HTTP transaction.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        req_id = getattr(request.state, "request_id", "none")
        client_ip = request.client.host if request.client else "127.0.0.1"

        logger.info(
            "[%s] %s %s - %d (%.1f ms) - %s",
            req_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_ip,
        )
        return response
