async def test_register_and_login(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "dev@example.com", "password": "s3cret-pass", "full_name": "Dev Tester"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "dev@example.com"
    assert "referral_code" in body

    resp = await client.post("/auth/login", data={"username": "dev@example.com", "password": "s3cret-pass"})
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"email": "a@example.com", "password": "correct-pass"})
    resp = await client.post("/auth/login", data={"username": "a@example.com", "password": "wrong"})
    assert resp.status_code == 401


async def test_duplicate_registration_rejected(client):
    await client.post("/auth/register", json={"email": "dup@example.com", "password": "correct-pass"})
    resp = await client.post("/auth/register", json={"email": "dup@example.com", "password": "another-pass"})
    assert resp.status_code == 400


async def test_refresh_token_issues_new_pair(client):
    await client.post("/auth/register", json={"email": "refresh@example.com", "password": "correct-pass"})
    login_resp = await client.post(
        "/auth/login", data={"username": "refresh@example.com", "password": "correct-pass"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/auth/refresh", params={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
