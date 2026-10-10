from app.core.settings import settings


def test_me_requires_sign_in(client):
    assert client.get("/auth/me").status_code == 401


def test_forged_token_is_rejected(client):
    response = client.post("/auth/google", json={"credential": "forged"})
    assert response.status_code == 401


def test_unverified_email_is_rejected(client, google_user):
    google_user["email_verified"] = False
    response = client.post("/auth/google", json={"credential": "any"})
    assert response.status_code == 401


def test_sign_in_me_and_sign_out(client, google_user):
    response = client.post("/auth/google", json={"credential": "any"})
    assert response.status_code == 200
    assert response.json()["email"] == google_user["email"]
    assert "google_sub" not in response.json()

    old_cookie = client.cookies.get(settings.session_cookie_name)
    assert old_cookie
    assert client.get("/auth/me").status_code == 200

    assert client.post("/auth/logout").status_code == 204
    assert client.cookies.get(settings.session_cookie_name) is None

    client.cookies.set(settings.session_cookie_name, old_cookie)
    assert client.get("/auth/me").status_code == 401


def test_signing_in_twice_keeps_one_user(client, google_user):
    first = client.post("/auth/google", json={"credential": "any"}).json()
    second = client.post("/auth/google", json={"credential": "any"}).json()
    assert first["id"] == second["id"]


def test_other_origin_is_rejected(client):
    response = client.post("/auth/logout", headers={"Origin": "https://evil.example"})
    assert response.status_code == 403


def test_own_origin_is_accepted(client):
    response = client.post("/auth/logout", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 204
