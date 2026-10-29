import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "screening-api"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_login_success_username(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={
        "username": "officer",
        "password": "OfficerSecure2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "officer"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_rejects_email_requires_username(client: AsyncClient):
    # Only username 'officer' is accepted; email 'officer@demo.com' is rejected
    res = await client.post("/api/v1/auth/login", json={
        "username": "officer@demo.com",
        "password": "OfficerSecure2026!"
    })
    assert res.status_code == 401
    assert res.json()["error"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={
        "username": "officer",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert res.json()["error"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={
        "username": "unknown_user",
        "password": "AnyPassword!"
    })
    assert res.status_code == 401
    assert res.json()["error"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_role_based_access_control(client: AsyncClient, officer_token: str, admin_token: str):
    # Create a screening first as officer
    files = {"file": ("test.jpg", b"sample image bytes", "image/jpeg")}
    data = {"document_type": "passport"}
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "test-key-rbac-1"
    }
    upload_res = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert upload_res.status_code == 202
    screening_id = upload_res.json()["screening_id"]

    # Admin cannot post review (403 Forbidden)
    admin_review_res = await client.post(
        f"/api/v1/screenings/{screening_id}/review",
        json={"decision": "confirmed", "notes": "Admin attempting review that should fail"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_review_res.status_code == 403
    assert admin_review_res.json()["error"] == "FORBIDDEN"

    # Officer can post review
    officer_review_res = await client.post(
        f"/api/v1/screenings/{screening_id}/review",
        json={"decision": "confirmed", "notes": "Officer valid review notes with at least 10 chars"},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert officer_review_res.status_code == 201
    assert officer_review_res.json()["decision"] == "confirmed"


@pytest.mark.asyncio
async def test_cors_preflight_and_headers(client: AsyncClient):
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization, idempotency-key, content-type",
    }
    res = await client.options("/api/v1/screenings", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"
    allow_headers = res.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allow_headers
    assert "idempotency-key" in allow_headers

