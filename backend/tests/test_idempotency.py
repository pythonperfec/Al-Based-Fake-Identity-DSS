import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_idempotent_submission(client: AsyncClient, officer_token: str):
    headers = {
        "Authorization": f"Bearer {officer_token}",
        "Idempotency-Key": "unique-idempotency-key-100"
    }
    files = {"file": ("doc.jpg", b"sample doc bytes", "image/jpeg")}
    data = {"document_type": "national_id"}

    # First request
    res1 = await client.post("/api/v1/screenings", files=files, data=data, headers=headers)
    assert res1.status_code == 202
    body1 = res1.json()
    screening_id_1 = body1["screening_id"]

    # Replay request with same idempotency key and same user
    files2 = {"file": ("doc.jpg", b"sample doc bytes", "image/jpeg")}
    res2 = await client.post("/api/v1/screenings", files=files2, data=data, headers=headers)
    # Should return existing screening without failing
    assert res2.status_code in [200, 202]
    body2 = res2.json()
    assert body2["screening_id"] == screening_id_1

    # Verify screenings list has only 1 screening created
    list_res = await client.get("/api/v1/screenings", headers={"Authorization": f"Bearer {officer_token}"})
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1


@pytest.mark.asyncio
async def test_idempotency_key_isolation_between_different_users(
    client: AsyncClient, officer_token: str, admin_token: str
):
    shared_key = "cross-user-idempotency-key"
    files = {"file": ("doc.png", b"sample png bytes", "image/png")}
    data = {"document_type": "passport"}

    # User 1 (officer) submits
    res1 = await client.post(
        "/api/v1/screenings",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {officer_token}", "Idempotency-Key": shared_key}
    )
    assert res1.status_code == 202
    screening_id_1 = res1.json()["screening_id"]

    # User 2 (admin) submits with the exact same Idempotency-Key
    files2 = {"file": ("doc.png", b"sample png bytes", "image/png")}
    res2 = await client.post(
        "/api/v1/screenings",
        files=files2,
        data=data,
        headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": shared_key}
    )
    assert res2.status_code == 202
    screening_id_2 = res2.json()["screening_id"]

    # Different user MUST NOT receive the first user's screening
    assert screening_id_1 != screening_id_2

    # Verify 2 distinct screenings were created in total
    list_res = await client.get("/api/v1/screenings", headers={"Authorization": f"Bearer {officer_token}"})
    assert list_res.json()["total"] == 2

