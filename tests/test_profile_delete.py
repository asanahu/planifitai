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
    test_client.post("/api/v1/profile", json=profile_data, headers=headers)
    response = test_client.delete("/api/v1/profile", headers=headers)
    assert response.status_code == 204
    response = test_client.get("/api/v1/profile/me", headers=headers)
    assert response.status_code == 404
