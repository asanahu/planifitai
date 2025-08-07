from celery import Celery


def create_celery() -> Celery:
    celery_app = Celery("planifitai")
    celery_app.autodiscover_tasks(["app.ai_assistant"])
    return celery_app