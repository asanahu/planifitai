from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core.config import settings
from app.security.crypto import reset_crypto_provider
from scripts.rotate_phi_key import rotate_phi_key


def _auth_header(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_phi_encryption_roundtrip(test_client, db_session, tokens):
    payload = {
        "full_name": "John Doe",
        "age": 30,
        "height_cm": 176.0,
        "weight_kg": 81.5,
        "medical_conditions": "asthma",
        "activity_level": "sedentary",
        "goal": "maintain_weight",
    }
    resp = test_client.post(
        "/api/v1/profiles/", json=payload, headers=_auth_header(tokens)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["weight_kg"] == payload["weight_kg"]
    assert data["height_cm"] == payload["height_cm"]
    assert data["medical_conditions"] == payload["medical_conditions"]

    row = db_session.execute(
        text(
            "SELECT weight_kg, height_cm, medical_conditions FROM user_profiles WHERE id=:id"
        ),
        {"id": data["id"]},
    ).first()
    assert b"81.5" not in row[0]
    assert b"176" not in row[1]
    assert b"asthma" not in row[2]


def test_phi_key_rotation(test_client, db_session, tokens):
    payload = {
        "full_name": "Jane Roe",
        "age": 25,
        "height_cm": 170.0,
        "weight_kg": 60.2,
        "medical_conditions": "none",
        "activity_level": "sedentary",
        "goal": "maintain_weight",
    }
    resp = test_client.post(
        "/api/v1/profiles/", json=payload, headers=_auth_header(tokens)
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]

    raw_before = db_session.execute(
        text("SELECT weight_kg FROM user_profiles WHERE id=:id"), {"id": pid}
    ).scalar()
    old_key = settings.PHI_ENCRYPTION_KEY
    new_key = Fernet.generate_key().decode()

    rotate_phi_key(old_key, new_key, db_session)
    db_session.expire_all()

    # Switch provider to new key
    settings.PHI_ENCRYPTION_KEY = new_key
    reset_crypto_provider()

    raw_after = db_session.execute(
        text("SELECT weight_kg FROM user_profiles WHERE id=:id"), {"id": pid}
    ).scalar()
    assert raw_before != raw_after

    resp2 = test_client.get(f"/api/v1/profiles/{pid}", headers=_auth_header(tokens))
    assert resp2.status_code == 200
    assert resp2.json()["weight_kg"] == payload["weight_kg"]
