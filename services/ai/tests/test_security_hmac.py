import json
import hmac
import time
from hashlib import sha256
import os
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient
import types
import sys

os.environ["AI_INTERNAL_SECRET"] = "testsecret"

service_root = Path(__file__).resolve().parents[1]
pkg = types.ModuleType("ai_service")
pkg.__path__ = [str(service_root / "app")]
sys.modules["ai_service"] = pkg
spec = importlib.util.spec_from_file_location(
    "ai_service.main", service_root / "app" / "main.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules["ai_service.main"] = module
spec.loader.exec_module(module)
app = module.app

client = TestClient(app, raise_server_exceptions=False)


def _sign(ts: str, body: str) -> str:
    msg = f"{ts}.{body}".encode()
    return hmac.new(b"testsecret", msg, sha256).hexdigest()


def test_valid_signature():
    ts = str(int(time.time()))
    body = json.dumps({"texts": ["hola"]})
    sig = _sign(ts, body)
    resp = client.post(
        "/v1/embeddings",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Internal-Signature": sig,
        },
    )
    assert resp.status_code == 200


def test_invalid_signature():
    ts = str(int(time.time()))
    body = json.dumps({"texts": ["hola"]})
    resp = client.post(
        "/v1/embeddings",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Internal-Signature": "bad",
        },
    )
    assert resp.status_code == 401


def test_old_timestamp():
    ts = str(int(time.time()) - 120)
    body = json.dumps({"texts": ["hola"]})
    sig = _sign(ts, body)
    resp = client.post(
        "/v1/embeddings",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Internal-Signature": sig,
        },
    )
    assert resp.status_code == 401
