import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_missing_idempotency_key(client: AsyncClient, officer_token: str):
    files = {"file": ("test.png", b"test bytes", "image/png")}
    data = {"document_type": "passport"}
    headers = {"Authorization": f"Bearer {officer_token}"}  # No Idempotency-Key

    res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert res.status_code == 400
    assert res.json()["error"] == "IDEMPOTENCY_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_upload_invalid_document_type(client: AsyncClient, officer_token: str):
    files = {"file": ("test.jpg", b"test bytes", "image/jpeg")}
    data = {"document_type": "driver_license"}  # Not in ["passport", "national_id"]
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-invalid-type"
    }

    res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert res.status_code == 400
    assert res.json()["error"] == "INVALID_DOCUMENT_TYPE"


@pytest.mark.asyncio
async def test_upload_unsupported_media_type(client: AsyncClient, officer_token: str):
    # Test plain text
    files = {"file": ("test.txt", b"plain text content", "text/plain")}
    data = {"document_type": "passport"}
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-invalid-mime"
    }

    res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert res.status_code == 415
    assert res.json()["error"] == "UNSUPPORTED_MEDIA_TYPE"

    # Test PDF (explicitly rejected per contract)
    pdf_files = {"file": ("document.pdf", b"%PDF-1.4 sample content", "application/pdf")}
    pdf_headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-pdf-mime"
    }
    pdf_res = await client.post("/api/v1/screenings", files=pdf_files, data=data, headers=pdf_headers)
    assert pdf_res.status_code == 415
    assert pdf_res.json()["error"] == "UNSUPPORTED_MEDIA_TYPE"


@pytest.mark.asyncio
async def test_upload_file_too_large(client: AsyncClient, officer_token: str):
    # Over 10 MB: 10 * 1024 * 1024 + 10 bytes
    large_bytes = b"0" * (10 * 1024 * 1024 + 10)
    files = {"file": ("huge.jpg", large_bytes, "image/jpeg")}
    data = {"document_type": "passport"}
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-too-large"
    }

    res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert res.status_code == 413
    assert res.json()["error"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_upload_success(client: AsyncClient, officer_token: str):
    files = {"file": ("valid.png", b"\x89PNG\r\n\x1a\nfakeimagebytes", "image/png")}
    data = {"document_type": "passport"}
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-success-1"
    }

    res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert res.status_code == 202
    body = res.json()
    assert "screening_id" in body
    assert body["status"] == "queued"
    assert body["document_type"] == "passport"

