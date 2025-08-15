from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_user(test_client: TestClient):
    response = test_client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "string"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"


def test_login(test_client: TestClient):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "test2@example.com", "password": "string"},
    )
    response = test_client.post(
        "/api/v1/auth/login",
        data={"username": "test2@example.com", "password": "string"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_create_profile(test_client: TestClient):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "test3@example.com", "password": "string"},
    )
    login_response = test_client.post(
        "/api/v1/auth/login",
        data={"username": "test3@example.com", "password": "string"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    profile_data = {
        "full_name": "Test User",
        "age": 30,
        "height_cm": 180,
        "weight_kg": 75,
        "activity_level": "moderately_active",
        "goal": "maintain_weight",
    }
    response = test_client.post("/api/v1/profiles/", json=profile_data, headers=headers)
    assert response.status_code == 201
    assert response.json()["full_name"] == "Test User"


def test_get_profile(test_client: TestClient):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "test4@example.com", "password": "string"},
    )
    login_response = test_client.post(
        "/api/v1/auth/login",
        data={"username": "test4@example.com", "password": "string"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    profile_data = {
        "full_name": "Test User 2",
        "age": 25,
        "height_cm": 170,
        "weight_kg": 65,
        "activity_level": "lightly_active",
        "goal": "lose_weight",
    }
    res = test_client.post("/api/v1/profiles/", json=profile_data, headers=headers)
    profile_id = res.json()["id"]
    response = test_client.get(f"/api/v1/profiles/{profile_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test User 2"


def test_update_profile(test_client: TestClient):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "test5@example.com", "password": "string"},
    )
    login_response = test_client.post(
        "/api/v1/auth/login",
        data={"username": "test5@example.com", "password": "string"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    profile_data = {
        "full_name": "Test User 3",
        "age": 40,
        "height_cm": 190,
        "weight_kg": 85,
        "activity_level": "very_active",
        "goal": "gain_weight",
    }
    res = test_client.post("/api/v1/profiles/", json=profile_data, headers=headers)
    profile_id = res.json()["id"]
    update_data = {"full_name": "Updated Test User"}
    response = test_client.put(
        f"/api/v1/profiles/{profile_id}", json=update_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Test User"
