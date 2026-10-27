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



@pytest.mark.asyncio
async def test_self_service_user_registration(client: AsyncClient):
    """Verify any new clinical personnel can self-register with DPDP consent and receive a JWT session."""
    reg_payload = {
        "username": "sjenkins",
        "email": "sarah.jenkins@pharma-iq.internal",
        "password": "SecurePassword2026!",
        "full_name": "Dr. Sarah Jenkins",
        "role": "quality_assurance",
        "department": "Solid Dosage Facility",
        "terms_accepted": True,
        "privacy_consent": True,
        "policy_version": "v1.0-2026",
    }
    res = await client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "sjenkins"
    assert data["user"]["full_name"] == "Dr. Sarah Jenkins"
    assert data["user"]["role"] == "quality_assurance"
    assert data["user"]["dpdp_consent_granted"] is True

    # Verify newly registered user can also log in immediately via /login
    login_res = await client.post(
        "/api/auth/login",
        json={"username": "sjenkins", "password": "SecurePassword2026!"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["username"] == "sjenkins"


@pytest.mark.asyncio
async def test_registration_without_affirmative_consent_rejected(client: AsyncClient):
    """Verify registration without DPDP Act Section 6 affirmative consent is rejected with 422."""
    reg_payload = {
        "username": "noconsent_user",
        "email": "noconsent@pharma-iq.internal",
        "password": "SecurePassword2026!",
        "full_name": "No Consent Person",
        "role": "technician",
        "terms_accepted": False,
        "privacy_consent": False,
    }
    res = await client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 422
    assert "affirmative consent" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_registration_duplicate_username_conflict(client: AsyncClient):
    """Verify duplicate username or email registration returns HTTP 409 Conflict."""
    reg_payload = {
        "username": "qa_officer",  # already exists from seed
        "email": "another.email@pharma.com",
        "password": "Password1234!",
        "full_name": "Duplicate Operator",
        "role": "technician",
        "terms_accepted": True,
        "privacy_consent": True,
    }
    res = await client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]


@pytest.mark.asyncio
async def test_statutory_compliance_policies(client: AsyncClient):
    """Verify DPDP Act 2023, IT Act 2000, and Cookie Policy endpoints return 200 with required legal terms."""
    # 1. Privacy Policy (DPDP Act §5 Notice)
    res_privacy = await client.get("/api/compliance/privacy-policy")
    assert res_privacy.status_code == 200
    priv_data = res_privacy.json()
    assert "Digital Personal Data Protection Act, 2023" in priv_data["governing_law"]
    assert any("Data Fiduciary" in s["heading"] or "Data Fiduciary" in s["content"] for s in priv_data["sections"])

    # 2. Terms and Conditions (IT Act 2000)
    res_terms = await client.get("/api/compliance/terms-and-conditions")
    assert res_terms.status_code == 200
    terms_data = res_terms.json()
    assert "Information Technology Act, 2000" in terms_data["governing_law"]
    assert any("21 CFR Part 11" in s["heading"] or "Electronic Record" in s["heading"] for s in terms_data["sections"])

    # 3. Cookie Policy
    res_cookies = await client.get("/api/compliance/cookie-policy")
    assert res_cookies.status_code == 200
    assert any("Strictly Essential" in s["heading"] for s in res_cookies.json()["sections"])

    # 4. Data Protection Officer (DPDP Act §13)
    res_dpo = await client.get("/api/compliance/dpo-contact")
    assert res_dpo.status_code == 200
    dpo_data = res_dpo.json()
    assert "dpo-compliance@deviationiq.internal" in dpo_data["email"]
    assert dpo_data["statutory_response_days"] == 30


@pytest.mark.asyncio
async def test_data_subject_right_to_access_and_erasure(client: AsyncClient):
    """Verify DPDP Act 2023 Section 11 Right to Access and Section 12 Right to Erasure workflows."""
    # 1. Register a data principal
    user_reg = {
        "username": "dataprinci_user",
        "email": "principal@pharmagov.in",
        "password": "CompliantPass2026!",
        "full_name": "Rohan Deshmukh",
        "role": "technician",
        "department": "Formulations Unit 3",
        "terms_accepted": True,
        "privacy_consent": True,
    }
    reg_res = await client.post("/api/auth/register", json=user_reg)
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Right to Access (DPDP Act §11)
    access_res = await client.get("/api/compliance/my-data", headers=headers)
    assert access_res.status_code == 200
    access_data = access_res.json()
    assert access_data["user_profile"]["username"] == "dataprinci_user"
    assert access_data["dpdp_consent_granted"] is True
    assert len(access_data["consents"]) >= 2  # terms + privacy recorded on register

    # 3. Log an additional cookie consent record
    cookie_consent_res = await client.post(
        "/api/compliance/consent",
        headers=headers,
        json={"consent_type": "essential_cookies", "granted": True},
    )
    assert cookie_consent_res.status_code == 200
    assert cookie_consent_res.json()["consent_type"] == "essential_cookies"

    # 4. Right to Erasure (DPDP Act §12)
    erasure_res = await client.post(
        "/api/compliance/erasure-request",
        headers=headers,
        json={
            "reason": "Relocating to another facility",
            "confirm_understanding": True,
        },
    )
    assert erasure_res.status_code == 200
    assert erasure_res.json()["status"] == "acknowledged"

    # 5. Verify account is now deactivated
    me_after = await client.get("/api/auth/me", headers=headers)
    assert me_after.status_code == 401
    assert "deactivated" in me_after.json()["detail"].lower()
