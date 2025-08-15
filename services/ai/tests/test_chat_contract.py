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


def _sign(body: str) -> dict:
    ts = str(int(time.time()))
    sig = hmac.new(b"testsecret", f"{ts}.{body}".encode(), sha256).hexdigest()
    return {
        "X-Timestamp": ts,
        "X-Internal-Signature": sig,
        "Content-Type": "application/json",
    }


def test_chat_reply_present():
    body = json.dumps({"messages": [{"role": "user", "content": "hola"}]})
    headers = _sign(body)
    resp = client.post("/v1/chat", data=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["reply"]
