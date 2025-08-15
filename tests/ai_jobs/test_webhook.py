from __future__ import annotations

import hmac
import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from fastapi.testclient import TestClient

from app.main import app


class _Handler(BaseHTTPRequestHandler):
    store: dict = {}

    def do_POST(self):  # noqa: N802
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)
        _Handler.store = {"headers": dict(self.headers), "body": body}
        self.send_response(200)
        self.end_headers()


def test_webhook_notification():
    server = HTTPServer(("127.0.0.1", 18080), _Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    client = TestClient(app)
    res = client.post(
        "/api/v1/ai/jobs/embeddings",
        json={"texts": ["hola"], "callback_url": "http://127.0.0.1:18080/cb"},
    )
    assert res.status_code == 202

    server.shutdown()
    thread.join()

    data = _Handler.store
    assert data
    headers = data["headers"]
    body = data["body"]
    expected = hmac.new(
        b"shh",
        f"{headers['X-Timestamp']}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()
    assert headers["X-Internal-Signature"] == expected
    payload = json.loads(body)
    assert payload["task_id"] == res.json()["task_id"]
    assert payload["state"] == "SUCCESS"
