async def _auth_headers(client, email="priv@example.com", password="pass1234"):
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_export_contains_profile_and_consent(client):
    headers = await _auth_headers(client)
    resp = await client.get("/privacy/export", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["profile"]["email"] == "priv@example.com"
    assert any(c["type"] == "data_processing" and c["granted"] for c in body["consents"])


async def test_withdraw_consent(client):
    headers = await _auth_headers(client, email="withdraw@example.com")
    resp = await client.post(
        "/privacy/consent/withdraw", json={"consent_type": "marketing"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "withdrawn"


async def test_deletion_revokes_access(client):
    headers = await _auth_headers(client, email="delete@example.com")

    resp = await client.post("/privacy/delete-request", headers=headers)
    assert resp.status_code == 200

    # The JWT itself is still technically valid and unexpired, but the user
    # is now inactive, so it must stop working.
    resp = await client.get("/privacy/export", headers=headers)
    assert resp.status_code == 401


async def test_deleted_email_can_reregister(client):
    email = "recycle@example.com"
    headers = await _auth_headers(client, email=email)
    await client.post("/privacy/delete-request", headers=headers)

    # Anonymization frees up the original email address for reuse.
    resp = await client.post("/auth/register", json={"email": email, "password": "new-password"})
    assert resp.status_code == 201
