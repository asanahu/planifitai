import time
from fastapi.testclient import TestClient


def test_refresh_returns_new_access_token(test_client: TestClient, tokens):
    refresh_token = tokens["refresh_token"]
    access_token = tokens["access_token"]
    time.sleep(1)
    response = test_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] != access_token


def test_refresh_rejects_access_token(test_client: TestClient, tokens):
    access_token = tokens["access_token"]
    response = test_client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_protected_rejects_refresh_token(test_client: TestClient, tokens):
    refresh_token = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = test_client.get("/api/v1/profiles/", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type for this operation"
