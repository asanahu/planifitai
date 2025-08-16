from fastapi.testclient import TestClient

from app.core.errors import AUTH_FORBIDDEN, COMMON_VALIDATION, PLAN_NOT_FOUND


def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_create_and_get_routine(test_client: TestClient, tokens):
    payload = {"name": "Routine A"}
    res = test_client.post(
        "/api/v1/routines/",
        json=payload,
        headers=auth_headers(tokens),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    routine_id = body["data"]["id"]

    res = test_client.get(
        f"/api/v1/routines/{routine_id}", headers=auth_headers(tokens)
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["data"]["id"] == routine_id

    res = test_client.get("/api/v1/routines/", headers=auth_headers(tokens))
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)


def test_get_routine_not_found(test_client: TestClient, tokens):
    res = test_client.get("/api/v1/routines/999", headers=auth_headers(tokens))
    assert res.status_code == 404
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == PLAN_NOT_FOUND


def test_create_routine_validation(test_client: TestClient, tokens):
    res = test_client.post(
        "/api/v1/routines/",
        json={},
        headers=auth_headers(tokens),
    )
    assert res.status_code == 422
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == COMMON_VALIDATION


def test_routines_forbidden(test_client: TestClient):
    res = test_client.get("/api/v1/routines/")
    assert res.status_code in (401, 403)
    body = res.json()
    assert body["ok"] is False
    assert body["error"]["code"] == AUTH_FORBIDDEN
