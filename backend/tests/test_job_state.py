import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.screening import Screening
from app.services.orchestrator import ScreeningOrchestrator
from tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_job_state_transitions_and_null_rules(client: AsyncClient, officer_token: str):
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-job-state-1"
    }
    files = {"file": ("doc.png", b"image binary content", "image/png")}
    data = {"document_type": "passport"}

    upload_res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert upload_res.status_code == 202
    screening_id = upload_res.json()["screening_id"]

    # Check state right after upload (or while queued/processing)
    async with TestAsyncSessionLocal() as session:
        stmt = select(Screening).where(Screening.id == screening_id)
        res = await session.execute(stmt)
        s = res.scalar_one()

        # Manually verify null rule in 'queued' state
        s.status = "queued"
        s.risk_level = "high"  # Even if DB has value, API must return null
        s.risk_score = 99.0
        await session.commit()

    detail_res = await client.get(f"/api/v1/screenings/{screening_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "queued"
    assert detail["risk_level"] is None
    assert detail["risk_score"] is None

    # Manually verify null rule in 'processing' state
    async with TestAsyncSessionLocal() as session:
        stmt = select(Screening).where(Screening.id == screening_id)
        res = await session.execute(stmt)
        s = res.scalar_one()
        s.status = "processing"
        await session.commit()

    detail_res = await client.get(f"/api/v1/screenings/{screening_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "processing"
    assert detail["risk_level"] is None
    assert detail["risk_score"] is None

    # Execute stub orchestrator to transition from processing -> incomplete (Phase 1 stub)
    orchestrator = ScreeningOrchestrator()
    async with TestAsyncSessionLocal() as session:
        await orchestrator.process_screening(screening_id, session)

    # Verify 'incomplete' state requirements per contract & invariant rules
    detail_res = await client.get(f"/api/v1/screenings/{screening_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "incomplete"
    assert detail["risk_level"] == "incomplete"
    assert detail["risk_score"] is None
    assert detail["reasons"] == ["Analysis pipeline not yet implemented"]
    assert len(detail["checks"]) == 8
    # Confirm NO check is "passed" and risk_level is never "low"
    for check in detail["checks"]:
        assert check["state"] == "not_performed"
        assert check["state"] != "passed"
    assert detail["risk_level"] != "low"

    # Verify masked document number in extracted_fields
    async with TestAsyncSessionLocal() as session:
        stmt = select(Screening).where(Screening.id == screening_id)
        res = await session.execute(stmt)
        s = res.scalar_one()
        s.extracted_fields = {"document_number": "P123456789"}
        await session.commit()

    detail_res = await client.get(f"/api/v1/screenings/{screening_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert detail_res.json()["extracted_fields"]["document_number"] == "******6789"


@pytest.mark.asyncio
async def test_case_audit_and_image_retrieval(client: AsyncClient, officer_token: str):
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-audit-img"
    }
    sample_bytes = b"my-image-bytes-for-screening"
    files = {"file": ("passport.jpg", sample_bytes, "image/jpeg")}
    data = {"document_type": "passport"}

    upload_res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert upload_res.status_code == 202
    screening_id = upload_res.json()["screening_id"]

    # Retrieve image
    img_res = await client.get(f"/api/v1/screenings/{screening_id}/image", headers={"Authorization": f"Bearer {officer_token}"})
    assert img_res.status_code == 200
    assert img_res.content == sample_bytes
    assert img_res.headers.get("cache-control") == "private, no-store"

    # Retrieve case audit
    audit_res = await client.get(f"/api/v1/cases/{screening_id}/audit", headers={"Authorization": f"Bearer {officer_token}"})
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["case_id"] == screening_id
    actions = [e["action"] for e in audit_data["events"]]
    assert "SCREENING_SUBMITTED" in actions
    assert "IMAGE_VIEWED" in actions

    # Retrieve findings (must write FINDINGS_VIEWED)
    findings_res = await client.get(f"/api/v1/screenings/{screening_id}/findings", headers={"Authorization": f"Bearer {officer_token}"})
    assert findings_res.status_code == 200
    assert findings_res.json()["screening_id"] == screening_id

    # Verify both IMAGE_VIEWED and FINDINGS_VIEWED are written to case audit
    audit_res_2 = await client.get(f"/api/v1/cases/{screening_id}/audit", headers={"Authorization": f"Bearer {officer_token}"})
    assert audit_res_2.status_code == 200
    all_actions = [e["action"] for e in audit_res_2.json()["events"]]
    assert "SCREENING_SUBMITTED" in all_actions
    assert "IMAGE_VIEWED" in all_actions
    assert "FINDINGS_VIEWED" in all_actions


@pytest.mark.asyncio
async def test_get_unknown_screening_returns_404_envelope(client: AsyncClient, officer_token: str):
    unknown_id = "00000000-0000-0000-0000-000000000000"
    res = await client.get(f"/api/v1/screenings/{unknown_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"] == "NOT_FOUND"
    assert "message" in data
    assert f"Screening '{unknown_id}' not found" in data["message"]
