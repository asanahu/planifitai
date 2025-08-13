from fastapi.testclient import TestClient


def test_create_single_entry_and_list(test_client: TestClient, tokens):
    access = tokens["access_token"]
    payload = {"date": "2024-01-01", "metric": "weight", "value": 80.0, "unit": "kg"}
    resp = test_client.post(
        "/api/v1/progress",
        json=payload,
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 1
    entry_id = data[0]["id"]

    resp = test_client.get(
        "/api/v1/progress",
        params={"metric": "weight"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["id"] == entry_id


def test_create_bulk_entries_and_summary(test_client: TestClient, tokens):
    access = tokens["access_token"]
    items = [
        {"date": "2024-01-01", "metric": "steps", "value": 1000},
        {"date": "2024-01-02", "metric": "steps", "value": 2000},
        {"date": "2024-01-03", "metric": "steps", "value": 1500},
    ]
    resp = test_client.post(
        "/api/v1/progress",
        json={"items": items},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 3

    resp = test_client.get(
        "/api/v1/progress/summary",
        params={"metric": "steps", "start": "2024-01-01", "end": "2024-01-03"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert data["min"] == 1000
    assert data["max"] == 2000
    assert data["avg"] == 1500
    assert data["first"] == 1000
    assert data["last"] == 1500
    assert data["delta"] == 500
