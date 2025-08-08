from celery import Celery

celery_app = Celery("planifitai")
celery_app.autodiscover_tasks(["app.ai_assistant"])