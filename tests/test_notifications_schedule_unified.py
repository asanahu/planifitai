import pytest
from fastapi.testclient import TestClient

from tests.test_routine_update_guards import routine_factory  # noqa: F401


def unwrap(j):
    return j.get("data", j)


@pytest.fixture
def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_canonical_schedules_ok(
    test_client: TestClient, routine_factory, auth_headers
):
    routine = routine_factory(active_days={"mon": True})
    resp = test_client.post(
        f"/api/v1/routines/{routine.id}/schedule-notifications", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    data = unwrap(resp.json())
    assert data.get("scheduled_count") is not None
    assert data.get("scheduled_count") >= 0


def test_duplicate_endpoint_deprecated_header_and_delegates(
    test_client: TestClient, routine_factory, auth_headers
):
    routine = routine_factory(active_days={"mon": True})
    resp = test_client.post(
        "/api/v1/notifications/schedule/routines",
        json={
            "routine_id": routine.id,
            "active_days": {"mon": True},
            "hour_local": "07:30",
        },
        headers=auth_headers,
    )
    if resp.status_code == 404:
        pytest.skip("no duplicate endpoint")
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("Deprecation")
    assert f"/api/v1/routines/{routine.id}/schedule-notifications" in resp.headers.get(
        "Link", ""
    )
    data = unwrap(resp.json())
    assert data.get("scheduled_count") is not None


def test_idempotent_across_both_endpoints(
    test_client: TestClient, routine_factory, auth_headers
):
    routine = routine_factory(active_days={"mon": True})
    first = test_client.post(
        f"/api/v1/routines/{routine.id}/schedule-notifications", headers=auth_headers
    )
    second = test_client.post(
        "/api/v1/notifications/schedule/routines",
        json={
            "routine_id": routine.id,
            "active_days": {"mon": True},
            "hour_local": "07:30",
        },
        headers=auth_headers,
    )
    if second.status_code == 404:
        pytest.skip("no duplicate endpoint")
    assert first.status_code == 200
    assert second.status_code == 200
    d1 = unwrap(first.json()).get("scheduled_count")
    d2 = unwrap(second.json()).get("scheduled_count")
    if d1 is not None and d2 is not None:
        assert d2 == 0 or d2 <= max(0, d1)
