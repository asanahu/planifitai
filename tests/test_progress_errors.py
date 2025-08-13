from fastapi.testclient import TestClient


def test_duplicate_entry_conflict(test_client: TestClient, tokens):
    access = tokens["access_token"]
    payload = {"date": "2024-01-01", "metric": "weight", "value": 80}
    resp1 = test_client.post(
        "/api/v1/progress",
        json=payload,
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp1.status_code == 201
    resp2 = test_client.post(
        "/api/v1/progress",
        json=payload,
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp2.status_code == 409


def test_list_with_date_filters(test_client: TestClient, tokens):
    access = tokens["access_token"]
    items = [
        {"date": "2024-01-01", "metric": "weight", "value": 70},
        {"date": "2024-01-02", "metric": "weight", "value": 71},
        {"date": "2024-01-03", "metric": "weight", "value": 72},
    ]
    test_client.post(
        "/api/v1/progress",
        json={"items": items},
        headers={"Authorization": f"Bearer {access}"},
    )
    resp = test_client.get(
        "/api/v1/progress",
        params={"metric": "weight", "start": "2024-01-02", "end": "2024-01-03"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = test_client.get(
        "/api/v1/progress",
        params={"start": "2024-01-03", "end": "2024-01-02"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 400


def test_delete_entry(test_client: TestClient, tokens):
    access = tokens["access_token"]
    payload = {"date": "2024-01-01", "metric": "weight", "value": 80}
    resp = test_client.post(
        "/api/v1/progress",
        json=payload,
        headers={"Authorization": f"Bearer {access}"},
    )
    entry_id = resp.json()[0]["id"]
    del_resp = test_client.delete(
        f"/api/v1/progress/{entry_id}",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert del_resp.status_code == 204
    del_again = test_client.delete(
        f"/api/v1/progress/{entry_id}",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert del_again.status_code == 404


def test_summary_requires_metric(test_client: TestClient, tokens):
    access = tokens["access_token"]
    resp = test_client.get(
        "/api/v1/progress/summary",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 422


def test_invalid_metric_validation(test_client: TestClient, tokens):
    access = tokens["access_token"]
    payload = {"date": "2024-01-01", "metric": "invalid", "value": 10}
    resp = test_client.post(
        "/api/v1/progress",
        json=payload,
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 422
