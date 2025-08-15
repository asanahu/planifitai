# AI Service

Simple FastAPI microservice exposing AI functionality used by the monolith.

## Environment variables

- `AI_INTERNAL_SECRET`: shared secret for HMAC authentication.

## Run locally

```
uvicorn app.main:app --reload --port 8080
```

## Example request

```
TS=$(date +%s)
BODY='{"texts": ["hola"]}'
SIG=$(python - <<PY
import hmac, os, sys, hashlib
secret=os.environ.get("AI_INTERNAL_SECRET","testsecret")
ts=os.environ["TS"]
body=os.environ["BODY"]
print(hmac.new(secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest())
PY)

curl -s -X POST http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "X-Timestamp: $TS" \
  -H "X-Internal-Signature: $SIG" \
  -d "$BODY"
```

The service exposes `/healthz` and `/readyz` endpoints for liveness and readiness checks.
