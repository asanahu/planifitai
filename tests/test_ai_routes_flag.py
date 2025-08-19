import importlib
import os

from fastapi.testclient import TestClient


def _reload_app_with_flag(value: bool):
    os.environ["AI_FEATURES_ENABLED"] = "true" if value else "false"
    import app.core.config as cfg
    importlib.reload(cfg)
    import app.main as m
    importlib.reload(m)
    return m.app


def _find_ai_route(app):
    for r in app.routes:
        p = getattr(r, "path", "")
        if p.startswith("/api/v1/ai/") and not p.startswith("/api/v1/ai/jobs"):
            methods = list(getattr(r, "methods", []) or [])
            return p, methods
    return None, None


def test_ai_disabled_returns_404_by_default():
    app = _reload_app_with_flag(False)
    client = TestClient(app)
    path, methods = _find_ai_route(app)
    assert path is None
    res = client.get("/api/v1/ai/ping")
    assert res.status_code == 404


def test_ai_enabled_exposes_routes():
    app = _reload_app_with_flag(True)
    client = TestClient(app)
    path, methods = _find_ai_route(app)
    assert path is not None and methods
    method = next(iter(methods))
    if method == "GET":
        res = client.get(path)
    elif method == "POST":
        res = client.post(path, json={})
    else:
        res = client.request(method, path)
    assert res.status_code in (200, 400, 422, 405)
