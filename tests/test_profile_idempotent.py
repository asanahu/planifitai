from fastapi.testclient import TestClient


def unwrap(j):
    return j.get("data", j)


def auth_hdr(tokens):
    try:
        from tests.utils import auth_headers as _auth_headers  # type: ignore

        return _auth_headers(tokens)
    except Exception:  # pragma: no cover - fallback
        return {"Authorization": f"Bearer {tokens['access_token']}"}


def profile_payload(goal="maintain_weight", age=30):
    return {
        "full_name": "John Doe",
        "age": age,
        "height_cm": 180,
        "weight_kg": 80,
        "activity_level": "sedentary",
        "goal": goal,
    }


def test_create_profile_double_post_is_idempotent(test_client: TestClient, tokens):
    payload = profile_payload()
    r1 = test_client.post("/api/v1/profiles/", json=payload, headers=auth_hdr(tokens))
    assert r1.status_code == 201, r1.text
    body1 = unwrap(r1.json())
    pid1 = body1["id"]
    assert pid1

    r2 = test_client.post("/api/v1/profiles/", json=payload, headers=auth_hdr(tokens))
    assert r2.status_code == 200, r2.text
    body2 = unwrap(r2.json())
    pid2 = body2["id"]
    assert pid2 == pid1
    assert body2["user_id"] == body1["user_id"]


def test_create_profile_second_payload_ignored(test_client: TestClient, tokens):
    payload_a = profile_payload(goal="lose_weight", age=25)
    payload_b = profile_payload(goal="gain_weight", age=40)

    r1 = test_client.post("/api/v1/profiles/", json=payload_a, headers=auth_hdr(tokens))
    assert r1.status_code == 201, r1.text
    body1 = unwrap(r1.json())
    pid1 = body1["id"]

    r2 = test_client.post("/api/v1/profiles/", json=payload_b, headers=auth_hdr(tokens))
    assert r2.status_code == 200, r2.text
    body2 = unwrap(r2.json())
    pid2 = body2["id"]
    assert pid2 == pid1
    # Ensure fields were not overwritten by second payload
    assert body2["goal"] == payload_a["goal"]
    assert body2["age"] == payload_a["age"]
