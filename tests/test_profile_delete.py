from fastapi.testclient import TestClient


def test_delete_profile_success(test_client: TestClient, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    profile_data = {
        "full_name": "Test User",
        "age": 30,
        "height_cm": 180,
        "weight_kg": 75,
        "activity_level": "moderately_active",
        "goal": "maintain_weight",
    }
    res = test_client.post("/api/v1/profiles/", json=profile_data, headers=headers)
    profile_id = res.json()["id"]
    response = test_client.delete(f"/api/v1/profiles/{profile_id}", headers=headers)
    assert response.status_code == 204
    response = test_client.get(f"/api/v1/profiles/{profile_id}", headers=headers)
    assert response.status_code == 404
