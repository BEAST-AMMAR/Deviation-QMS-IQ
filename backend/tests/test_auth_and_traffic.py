"""
Tests for Authentication, User Management, Rate Limiting & Overload Protection
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_seed_users_and_login_success(client: AsyncClient):
    """Verify default clinical staff can authenticate and receive JWT tokens."""
    res = await client.post(
        "/api/auth/login",
        json={"username": "qa_officer", "password": "PharmaQuality2026!"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "qa_officer"
    assert data["user"]["role"] == "quality_assurance"
    assert "Dr. Elena Vance" in data["user"]["full_name"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Verify invalid password returns 401 with appropriate message."""
    res = await client.post(
        "/api/auth/login",
        json={"username": "qa_officer", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert "Invalid clinical username or password" in res.json()["detail"]


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    """Verify unknown user returns 401."""
    res = await client.post(
        "/api/auth/login",
        json={"username": "ghost_operator", "password": "AnyPassword123!"},
    )
    assert res.status_code == 401
    assert "Invalid clinical username or password" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_with_bearer_token(client: AsyncClient):
    """Verify /api/auth/me returns authenticated user details when token is provided."""
    # 1. Login
    login_res = await client.post(
        "/api/auth/login",
        json={"username": "tech_lead", "password": "PharmaTech2026!"},
    )
    token = login_res.json()["access_token"]

    # 2. Query /me
    me_res = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user = me_res.json()
    assert user["username"] == "tech_lead"
    assert user["role"] == "technician"
    assert user["full_name"] == "Marcus Brody"


@pytest.mark.asyncio
async def test_get_me_without_token_unauthorized(client: AsyncClient):
    """Verify /api/auth/me rejects unauthenticated requests with 401."""
    res = await client.get("/api/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_correlation_id_header(client: AsyncClient):
    """Verify every request returns x-request-id in response headers."""
    res = await client.get("/health")
    assert res.status_code == 200
    assert "x-request-id" in res.headers
    assert res.headers["x-request-id"].startswith("req-")


@pytest.mark.asyncio
async def test_health_readiness_probe(client: AsyncClient):
    """Verify /health/ready confirms database liveness."""
    res = await client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_payload_size_limiter(client: AsyncClient):
    """Verify requests with Content-Length exceeding 25MB are dropped with 413."""
    oversized = 30 * 1024 * 1024  # 30 MB
    res = await client.post(
        "/api/drafts",
        headers={"Content-Length": str(oversized)},
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
