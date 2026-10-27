"""
DeviationIQ — Integration Tests for Drafts and Deviations API

Tests:
  - POST /api/drafts creates a draft with DB record
  - GET /api/drafts/{id} retrieves initial state
  - POST /api/drafts/{id}/message updates draft fields
  - POST /api/drafts/{id}/confirm commits record and blocks re-edits (SC-06, SC-07)
  - GET /api/deviations/{id} and /api/deviations/{id}/events returns committed record & audit trail
  - Read-only enforcement: attempting to confirm an already-committed draft returns 409
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_draft(client: AsyncClient):
    response = await client.post("/api/drafts")
    assert response.status_code == 200
    data = response.json()
    assert "draft_id" in data
    # Verify valid UUID
    draft_uuid = uuid.UUID(data["draft_id"])
    assert str(draft_uuid) == data["draft_id"]


@pytest.mark.asyncio
async def test_get_draft(client: AsyncClient):
    # 1. Create
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Get
    res_get = await client.get(f"/api/drafts/{draft_id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["draft_id"] == draft_id
    assert data["status"] == "draft"
    assert "fields" in data
    assert data["fields"]["site_plant"]["value"] is None


@pytest.mark.asyncio
async def test_reset_draft(client: AsyncClient):
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    res_reset = await client.post(f"/api/drafts/{draft_id}/reset")
    assert res_reset.status_code == 200
    data = res_reset.json()
    assert data["status"] == "reset"


@pytest.mark.asyncio
async def test_draft_message_and_confirm_lifecycle(client: AsyncClient):
    # 1. Create draft
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Post a message to graph (mock graph invocation)
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "current_fields": {
            "site_plant": {"value": "Hyderabad Unit 2", "confidence": "high", "origin": "ai"},
            "title": {"value": "Pressure surge in line 4", "confidence": "high", "origin": "ai"},
            "batch_lot": {"value": "LOT-8821", "confidence": "high", "origin": "ai"},
        },
        "changed_fields": ["site_plant", "title", "batch_lot"],
        "chat_reply": "Extracted fields from report.",
        "pending_assessment": {
            "suggested_severity": "Major",
            "suggested_impact": "Hold batch LOT-8821 for QA inspection",
            "reasoning": "Pressure surge exceeded 3.5 bar safety threshold",
        },
        "status": "pending_triage",
    }

    with patch("app.routers.drafts.get_compiled_graph", return_value=mock_graph):
        res_msg = await client.post(
            f"/api/drafts/{draft_id}/message",
            json={"text": "Pressure surge in line 4 at Hyderabad Unit 2, batch LOT-8821"},
        )
        assert res_msg.status_code == 200
        msg_data = res_msg.json()
        assert msg_data["fields"]["site_plant"]["value"] == "Hyderabad Unit 2"
        assert msg_data["pending_assessment"]["suggested_severity"] == "Major"

    # 3. Confirm assessment & commit deviation (Human confirmation gate — SAD §4)
    confirm_payload = {
        "suggested_severity": "Major",
        "suggested_impact": "Hold batch LOT-8821 for QA inspection",
        "reasoning": "Pressure surge exceeded safety limit",
        "reviewed_by": "Dr. Sarah Lin (QA Director)",
    }
    res_confirm = await client.post(
        f"/api/drafts/{draft_id}/confirm",
        json=confirm_payload,
    )
    assert res_confirm.status_code == 200
    confirm_data = res_confirm.json()
    assert confirm_data["status"] == "committed"
    assert confirm_data["deviation_id"] == draft_id

    # 4. SC-07 / R-04: Attempting to confirm again should be rejected with 409
    res_confirm_again = await client.post(
        f"/api/drafts/{draft_id}/confirm",
        json=confirm_payload,
    )
    assert res_confirm_again.status_code == 409

    # 5. Fetch committed deviation from /api/deviations/{id}
    res_dev = await client.get(f"/api/deviations/{draft_id}")
    assert res_dev.status_code == 200
    dev_data = res_dev.json()
    assert dev_data["id"] == draft_id
    assert dev_data["status"] == "committed"
    assert dev_data["site_plant"] == "Hyderabad Unit 2"
    assert dev_data["reviewed_by"] == "Dr. Sarah Lin (QA Director)"

    # 6. Verify audit trail events in /api/deviations/{id}/events
    res_events = await client.get(f"/api/deviations/{draft_id}/events")
    assert res_events.status_code == 200
    events = res_events.json()
    assert len(events) >= 1
    # Verify human confirmation event exists
    human_events = [e for e in events if e["actor"] == "human"]
    assert len(human_events) >= 1
    assert human_events[0]["field"] == "initial_severity"


@pytest.mark.asyncio
async def test_patch_draft_fields(client: AsyncClient):
    # 1. Create draft
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Patch single field
    res_patch1 = await client.patch(
        f"/api/drafts/{draft_id}/fields",
        json={"field_name": "site_plant", "value": "Goa Manufacturing Plant"},
    )
    assert res_patch1.status_code == 200
    fields_data = res_patch1.json()
    assert fields_data["site_plant"]["value"] == "Goa Manufacturing Plant"
    assert fields_data["site_plant"]["origin"] == "human"

    # 3. Patch bulk fields
    res_patch2 = await client.patch(
        f"/api/drafts/{draft_id}/fields",
        json={
            "fields": {
                "title": "Temperature Excursion in Cleanroom B",
                "batch_lot": "LOT-9901",
                "date_of_occurrence": "2026-09-27",
            }
        },
    )
    assert res_patch2.status_code == 200
    fields_data2 = res_patch2.json()
    assert fields_data2["title"]["value"] == "Temperature Excursion in Cleanroom B"
    assert fields_data2["batch_lot"]["value"] == "LOT-9901"
    assert fields_data2["date_of_occurrence"]["value"] == "2026-09-27"


@pytest.mark.asyncio
async def test_direct_commit_lifecycle(client: AsyncClient):
    # 1. Create draft
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Attempt commit with missing required fields -> 400 Bad Request
    res_fail = await client.post(
        f"/api/drafts/{draft_id}/commit",
        json={"title": "Incomplete deviation"},
    )
    assert res_fail.status_code == 400
    assert "Missing required fields" in res_fail.json()["detail"]

    # 3. Commit with all required fields
    full_payload = {
        "site_plant": "Vizag Formulation Site",
        "date_of_occurrence": "2026-09-25",
        "title": "Filter Integrity Test Failure",
        "source": "Lab Report",
        "related_product": "Saline Infusion 500ml",
        "batch_lot": "SL-4412",
        "detailed_description": "Post-filtration integrity test bubble point was below 3.2 bar specification at 2.9 bar.",
        "initial_impact": "Product Quality",
        "initial_severity": "Major",
        "reviewed_by": "Senior QA Officer Mark Davis",
        "reasoning": "Manual operator entry and verification of physical lab test sheet.",
    }
    res_commit = await client.post(
        f"/api/drafts/{draft_id}/commit",
        json=full_payload,
    )
    assert res_commit.status_code == 200
    commit_data = res_commit.json()
    assert commit_data["status"] == "committed"
    assert commit_data["deviation_id"] == draft_id

    # 4. Verify committed record in database via GET /api/deviations/{id}
    res_dev = await client.get(f"/api/deviations/{draft_id}")
    assert res_dev.status_code == 200
    dev = res_dev.json()
    assert dev["status"] == "committed"
    assert dev["site_plant"] == "Vizag Formulation Site"
    assert dev["date_of_occurrence"] == "2026-09-25"
    assert dev["initial_severity"] == "Major"
    assert dev["reviewed_by"] == "Senior QA Officer Mark Davis"

    # 5. Subsequent commit or patch attempts return 409 Conflict
    res_commit_repeat = await client.post(
        f"/api/drafts/{draft_id}/commit",
        json=full_payload,
    )
    assert res_commit_repeat.status_code == 409

    res_patch_locked = await client.patch(
        f"/api/drafts/{draft_id}/fields",
        json={"field_name": "title", "value": "Should be blocked"},
    )
    assert res_patch_locked.status_code == 409


@pytest.mark.asyncio
async def test_confirm_assessment_persists_date(client: AsyncClient):
    # 1. Create draft
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Set date and fields
    await client.patch(
        f"/api/drafts/{draft_id}/fields",
        json={
            "fields": {
                "site_plant": "Bengaluru Biologics",
                "date_of_occurrence": "2026-09-20",
                "title": "Bio-reactor temperature alarm",
                "source": "Shift Log",
                "detailed_description": "Bio-reactor temperature exceeded high limit for 12 minutes.",
            }
        },
    )

    # 3. Confirm assessment
    confirm_payload = {
        "suggested_severity": "Minor",
        "suggested_impact": "No impact on cell viability",
        "reasoning": "Quickly brought back into range within 12 minutes",
        "reviewed_by": "QA Lead",
    }
    res_confirm = await client.post(
        f"/api/drafts/{draft_id}/confirm",
        json=confirm_payload,
    )
    assert res_confirm.status_code == 200

    # 4. Check deviation date_of_occurrence is saved!
    res_dev = await client.get(f"/api/deviations/{draft_id}")
    assert res_dev.status_code == 200
    dev = res_dev.json()
    assert dev["date_of_occurrence"] == "2026-09-20"


@pytest.mark.asyncio
async def test_get_deviation_session_history(client: AsyncClient):
    # 1. Create draft
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Add message to draft (mock graph)
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "current_fields": {
            "site_plant": {"value": "Cork Sterile Facility", "confidence": "high"},
            "title": {"value": "Autoclave pressure sensor deviation", "confidence": "high"},
            "source": {"value": "Shift Log", "confidence": "high"},
            "date_of_occurrence": {"value": "2026-09-21", "confidence": "high"},
            "detailed_description": {"value": "Sensor PS-301 drifted 0.4 bar below calibrated threshold.", "confidence": "high"},
        },
        "changed_fields": ["site_plant", "title", "source", "date_of_occurrence", "detailed_description"],
        "chat_reply": "Fields successfully extracted from your autoclave report.",
        "pending_assessment": {
            "suggested_severity": "Minor",
            "suggested_impact": "Sensor recalibration before next run",
            "reasoning": "Batch cycle had already completed successfully",
        },
        "status": "awaiting_confirmation",
    }
    with patch("app.routers.drafts.get_compiled_graph", return_value=mock_graph):
        await client.post(
            f"/api/drafts/{draft_id}/message",
            json={"text": "Autoclave report: PS-301 pressure drifted at Cork Sterile Facility on 2026-09-21."},
        )

    # 3. Confirm & commit
    confirm_payload = {
        "suggested_severity": "Minor",
        "suggested_impact": "Sensor recalibration before next run",
        "reasoning": "Batch cycle had already completed successfully",
        "reviewed_by": "Compliance Lead Sarah",
    }
    res_confirm = await client.post(
        f"/api/drafts/{draft_id}/confirm",
        json=confirm_payload,
    )
    assert res_confirm.status_code == 200

    # 4. Fetch complete session history via /api/deviations/{id}/session
    res_session = await client.get(f"/api/deviations/{draft_id}/session")
    assert res_session.status_code == 200
    session_data = res_session.json()

    # Validate deviation record
    assert session_data["deviation"]["id"] == draft_id
    assert session_data["deviation"]["site_plant"] == "Cork Sterile Facility"
    assert session_data["deviation"]["initial_severity"] == "Minor"
    assert session_data["deviation"]["reviewed_by"] == "Compliance Lead Sarah"

    # Validate chat history transcript is preserved
    assert len(session_data["messages"]) >= 2
    chat_contents = [m["content"] for m in session_data["messages"]]
    assert any("Autoclave report" in c for c in chat_contents)
    assert any("Fields successfully extracted" in c for c in chat_contents)

    # Validate audit events
    assert len(session_data["events"]) >= 1

    # Validate session summary
    assert "Cork Sterile Facility" in session_data["session_summary"]
    assert "Minor" in session_data["session_summary"]


@pytest.mark.asyncio
async def test_export_deviation_pdf_and_docx(client: AsyncClient):
    """Test generating and downloading publication-grade PDF and DOCX reports."""
    # 1. Create draft and commit record
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    await client.patch(
        f"/api/drafts/{draft_id}/fields",
        json={
            "fields": {
                "site_plant": "Basel Formulation Center",
                "date_of_occurrence": "2026-09-26",
                "title": "Sterilizer gasket failure during batch cycle",
                "source": "Equipment Log",
                "detailed_description": "During run cycle 402, primary gasket degraded causing pressure release.",
                "initial_impact": "Batch segregated in cold store.",
                "initial_severity": "Critical",
            }
        },
    )

    res_commit = await client.post(
        f"/api/drafts/{draft_id}/commit",
        json={
            "title": "Sterilizer gasket failure during batch cycle",
            "site_plant": "Basel Formulation Center",
            "date_of_occurrence": "2026-09-26",
            "source": "Equipment Log",
            "detailed_description": "During run cycle 402, primary gasket degraded causing pressure release.",
            "initial_impact": "Batch segregated in cold store.",
            "initial_severity": "Critical",
            "reviewed_by": "Dr. Eleanor Vance",
        },
    )
    assert res_commit.status_code == 200

    # 2. Test PDF Export
    res_pdf = await client.get(f"/api/deviations/{draft_id}/export/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")
    assert len(res_pdf.content) > 1000

    # 3. Test DOCX Export
    res_docx = await client.get(f"/api/deviations/{draft_id}/export/docx")
    assert res_docx.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in res_docx.headers["content-type"]
    assert res_docx.content.startswith(b"PK\x03\x04")
    assert len(res_docx.content) > 2000





@pytest.mark.asyncio
async def test_root_and_health_endpoints(client: AsyncClient):
    """Verify system root discovery and health check endpoints."""
    # Test root
    res_root = await client.get("/")
    assert res_root.status_code == 200
    root_data = res_root.json()
    assert "DeviationIQ" in root_data["service"]
    assert root_data["status"] == "operational"
    assert "/docs" in root_data["endpoints"]["docs"]

    # Test /api/health
    res_api_health = await client.get("/api/health")
    assert res_api_health.status_code == 200
    assert res_api_health.json()["status"] == "healthy"

    # Test /health alias
    res_health = await client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_security_headers_middleware(client: AsyncClient):
    """Verify standard enterprise security headers are present on responses."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-origin" in response.headers.get("referrer-policy", "")


@pytest.mark.asyncio
async def test_get_draft_hydrates_from_db_on_empty_store(client: AsyncClient):
    """Verify draft state survives server restart or multi-worker state sync (NFR-02)."""
    from app.routers.drafts import _draft_store

    # 1. Create draft
    res_create = await client.post("/api/drafts")
    draft_id = res_create.json()["draft_id"]

    # 2. Patch fields to database
    await client.patch(
        f"/api/drafts/{draft_id}/fields",
        json={
            "fields": {
                "site_plant": "Dublin Bio Site",
                "title": "Sterility Chamber Pressure Drop",
                "batch_lot": "DUB-BIO-2026",
            }
        },
    )

    # 3. Simulate process restart or alternate worker by clearing in-memory store
    if draft_id in _draft_store:
        del _draft_store[draft_id]

    # 4. Fetch draft via GET /api/drafts/{id} — must hydrate from database!
    res_get = await client.get(f"/api/drafts/{draft_id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["draft_id"] == draft_id
    assert data["fields"]["site_plant"]["value"] == "Dublin Bio Site"
    assert data["fields"]["title"]["value"] == "Sterility Chamber Pressure Drop"
    assert data["fields"]["batch_lot"]["value"] == "DUB-BIO-2026"
