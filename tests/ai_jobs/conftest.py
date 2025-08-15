import os

import pytest
import redis

# Ensure Celery uses Redis and runs tasks eagerly
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
os.environ["AI_INTERNAL_SECRET"] = "shh"

from app.background.celery_app import celery_app  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_store_eager_result = True


@pytest.fixture(autouse=True)
def flush_redis():
    r = redis.from_url(os.environ["CELERY_BROKER_URL"])
    r.flushall()
    yield
    r.flushall()
