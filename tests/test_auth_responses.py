from fastapi.testclient import TestClient

from app.core.errors import AUTH_FORBIDDEN, AUTH_INVALID_CREDENTIALS


def test_login_valid(test_client: TestClient):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "u1@example.com", "password": "pw"},
    )
    res = test_client.post(
        "/api/v1/auth/login",
        data={"username": "u1@example.com", "password": "pw"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "access_token" in body["data"]


def test_refresh_valid(test_client: TestClient, tokens):
    res = test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "access_token" in body["data"]


def test_me_ok(test_client: TestClient, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    res = test_client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["email"] == "user@example.com"


def test_login_invalid(test_client: TestClient):
    res = test_client.post(
        "/api/v1/auth/login",
        data={"username": "no@user.com", "password": "bad"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == AUTH_INVALID_CREDENTIALS


def test_me_forbidden(test_client: TestClient):
    res = test_client.get("/api/v1/auth/me")
    assert res.status_code in (401, 403)
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == AUTH_FORBIDDEN


def test_refresh_invalid_token(test_client: TestClient):
    res = test_client.post("/api/v1/auth/refresh", json={"refresh_token": "x"})
    assert res.status_code == 401
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == AUTH_INVALID_CREDENTIALS
