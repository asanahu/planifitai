from fastapi.testclient import TestClient


def create_user_and_token(client: TestClient, email: str):
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": "string"})
    user_id = reg.json()["id"]
    login = client.post("/api/v1/auth/login", data={"username": email, "password": "string"})
    token = login.json()["access_token"]
    return user_id, token


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_idor_read(test_client: TestClient):
    user_a_id, token_a = create_user_and_token(test_client, "a@example.com")
    _, token_b = create_user_and_token(test_client, "b@example.com")

    profile_payload = {
        "full_name": "User A",
        "age": 30,
        "height_cm": 170,
        "weight_kg": 70,
        "activity_level": "sedentary",
        "goal": "maintain_weight",
    }
    res = test_client.post("/api/v1/profiles/", json=profile_payload, headers=auth_headers(token_a))
    profile_id = res.json()["id"]

    res_a = test_client.get(f"/api/v1/profiles/{profile_id}", headers=auth_headers(token_a))
    assert res_a.status_code == 200

    res_b = test_client.get(f"/api/v1/profiles/{profile_id}", headers=auth_headers(token_b))
    assert res_b.status_code == 404


def test_idor_update_delete_and_listing(test_client: TestClient):
    user_a_id, token_a = create_user_and_token(test_client, "c@example.com")
    _, token_b = create_user_and_token(test_client, "d@example.com")

    payload = {
        "full_name": "User C",
        "age": 25,
        "height_cm": 165,
        "weight_kg": 60,
        "activity_level": "lightly_active",
        "goal": "lose_weight",
    }
    res = test_client.post("/api/v1/profiles/", json=payload, headers=auth_headers(token_a))
    profile_id = res.json()["id"]

    # B cannot update
    res_b_update = test_client.put(
        f"/api/v1/profiles/{profile_id}",
        json={"full_name": "Hacker"},
        headers=auth_headers(token_b),
    )
    assert res_b_update.status_code == 404

    # B cannot delete
    res_b_del = test_client.delete(f"/api/v1/profiles/{profile_id}", headers=auth_headers(token_b))
    assert res_b_del.status_code == 404

    # Listing returns only own profile
    res_list_a = test_client.get("/api/v1/profiles/", headers=auth_headers(token_a))
    assert len(res_list_a.json()) == 1
    res_list_b = test_client.get("/api/v1/profiles/", headers=auth_headers(token_b))
    assert res_list_b.json() == []

    # A can delete
    res_del_a = test_client.delete(f"/api/v1/profiles/{profile_id}", headers=auth_headers(token_a))
    assert res_del_a.status_code == 204


def test_user_id_ignored_and_auth_required(test_client: TestClient):
    user_id, token = create_user_and_token(test_client, "e@example.com")
    payload = {
        "full_name": "User E",
        "age": 28,
        "height_cm": 175,
        "weight_kg": 68,
        "activity_level": "moderately_active",
        "goal": "gain_weight",
        "user_id": 999,
    }
    res = test_client.post("/api/v1/profiles/", json=payload, headers=auth_headers(token))
    assert res.status_code == 201
    data = res.json()
    assert data["user_id"] == user_id

    update_payload = {"user_id": 123, "full_name": "User E Updated"}
    res_update = test_client.put(
        f"/api/v1/profiles/{data['id']}",
        json=update_payload,
        headers=auth_headers(token),
    )
    assert res_update.status_code == 200
    assert res_update.json()["user_id"] == user_id
    assert res_update.json()["full_name"] == "User E Updated"

    res_unauth = test_client.get("/api/v1/profiles/")
    assert res_unauth.status_code == 401
