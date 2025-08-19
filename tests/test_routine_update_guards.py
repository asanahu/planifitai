import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.routines import models


def unwrap(j):
    return j.get("data", j)


def auth_hdr(tokens):
    try:
        from tests.utils import auth_headers as _auth_headers  # type: ignore
        return _auth_headers(tokens)
    except Exception:  # pragma: no cover - fallback
        return {"Authorization": f"Bearer {tokens['access_token']}"}


def _patch(client: TestClient, rid: int, payload: dict, tokens):
    return client.put(
        f"/api/v1/routines/{rid}", json=payload, headers=auth_hdr(tokens)
    )


def _soft_delete(db, routine):
    if hasattr(routine, "deleted_at"):
        routine.deleted_at = datetime.now(timezone.utc)
    elif hasattr(routine, "is_deleted"):
        routine.is_deleted = True  # type: ignore[attr-defined]
    else:  # pragma: no cover - model without soft delete flag
        pytest.skip("Soft-delete flag not found on Routine model")
    db.add(routine)
    db.commit()
    db.refresh(routine)


def _pause(db, routine):
    if hasattr(routine, "active"):
        routine.active = False  # type: ignore[attr-defined]
    elif hasattr(routine, "status"):
        routine.status = "paused"  # type: ignore[attr-defined]
    else:  # pragma: no cover - model without pause flag
        pytest.skip("Pause flag not found on Routine model")
    db.add(routine)
    db.commit()
    db.refresh(routine)


@pytest.fixture
def routine_factory(test_client: TestClient, tokens, db_session):
    def factory(**attrs):
        payload = {"name": f"R-{uuid.uuid4().hex[:6]}", "description": ""}
        payload.update(attrs)
        resp = test_client.post(
            "/api/v1/routines/", json=payload, headers=auth_hdr(tokens)
        )
        assert resp.status_code == 200, resp.text
        rid = unwrap(resp.json()).get("id")
        routine = db_session.query(models.Routine).filter_by(id=rid).first()
        db_session.refresh(routine)
        return routine

    return factory


def test_update_soft_deleted_returns_404(
    test_client: TestClient, db_session, routine_factory, tokens
):
    routine = routine_factory()
    _soft_delete(db_session, routine)
    r = _patch(test_client, routine.id, {"name": "Renamed"}, tokens)
    assert r.status_code == 404, r.text


def test_update_paused_returns_409(
    test_client: TestClient, db_session, routine_factory, tokens
):
    routine = routine_factory()
    _pause(db_session, routine)
    r = _patch(test_client, routine.id, {"name": "Renamed"}, tokens)
    assert r.status_code == 409, r.text


def test_update_active_ok_200(test_client: TestClient, routine_factory, tokens):
    routine = routine_factory()
    r = _patch(test_client, routine.id, {"name": "New Name"}, tokens)
    assert r.status_code == 200, r.text
    data = unwrap(r.json())
    new_name = data.get("name") or data.get("routine", {}).get("name")
    assert new_name in ("New Name",)


def test_update_ignores_protected_fields(
    test_client: TestClient, db_session, routine_factory, tokens
):
    routine = routine_factory()
    original_id = routine.id
    original_owner = routine.owner_id
    r = _patch(
        test_client,
        routine.id,
        {"id": 9999, "owner_id": 9999, "name": "Allowed"},
        tokens,
    )
    assert r.status_code == 200, r.text
    db_session.refresh(routine)
    assert routine.id == original_id
    assert routine.owner_id == original_owner
    assert routine.name == "Allowed"
