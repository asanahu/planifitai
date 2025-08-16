from __future__ import annotations

import os
from celery import Celery


def make_celery() -> Celery:
    broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    app = Celery(
        "planifitai",
        broker=broker,
        backend=backend,
        include=["app.background.tasks"],
    )
    if os.getenv("CELERY_TASK_ALWAYS_EAGER") == "1":
        app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
            result_backend="cache+memory://",
        )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "60")),
        task_soft_time_limit=int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "50")),
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        broker_transport_options={"visibility_timeout": 3600},
        result_expires=86400,
    )
    return app


celery_app = make_celery()
