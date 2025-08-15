from celery import Celery

celery_app = Celery("planifitai")
celery_app.conf.task_always_eager = True
celery_app.autodiscover_tasks(["app.ai_assistant", "app.notifications"])
