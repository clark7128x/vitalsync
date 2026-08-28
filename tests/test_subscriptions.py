async def _auth_headers(client, email="sub@example.com", password="pass1234"):
    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_subscription(client):
    headers = await _auth_headers(client)
    resp = await client.post("/subscriptions", json={"plan": "monthly"}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["plan"] == "monthly"
    assert body["status"] == "trialing"


async def test_cannot_double_subscribe(client):
    headers = await _auth_headers(client, email="dup@example.com")
    await client.post("/subscriptions", json={"plan": "monthly"}, headers=headers)
    resp = await client.post("/subscriptions", json={"plan": "monthly"}, headers=headers)
    assert resp.status_code == 400


async def test_upgrade_subscription(client):
    headers = await _auth_headers(client, email="upgrade@example.com")
    await client.post("/subscriptions", json={"plan": "monthly"}, headers=headers)

    resp = await client.post("/subscriptions/me/upgrade", json={"plan": "annual"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "annual"
    assert body["status"] == "active"


async def test_cancel_subscription(client):
    headers = await _auth_headers(client, email="cancel@example.com")
    await client.post("/subscriptions", json={"plan": "monthly"}, headers=headers)

    resp = await client.post("/subscriptions/me/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "canceled"

    # Canceled subscriptions don't block a fresh one.
    resp = await client.post("/subscriptions", json={"plan": "monthly"}, headers=headers)
    assert resp.status_code == 201


async def test_subscription_requires_auth(client):
    resp = await client.post("/subscriptions", json={"plan": "monthly"})
    assert resp.status_code == 401
