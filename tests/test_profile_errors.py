from fastapi.testclient import TestClient


def test_create_profile_twice_conflict(test_client: TestClient, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    profile_data = {
        "full_name": "User",
        "age": 25,
        "height_cm": 170,
        "weight_kg": 65,
        "activity_level": "lightly_active",
        "goal": "lose_weight",
    }
    test_client.post("/api/v1/profiles/", json=profile_data, headers=headers)
    response = test_client.post("/api/v1/profiles/", json=profile_data, headers=headers)
    assert response.status_code == 409


def test_patch_profile_not_found(test_client: TestClient, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = test_client.put("/api/v1/profiles/1", json={"full_name": "New"}, headers=headers)
    assert response.status_code == 404
