from app.background.celery_app import celery_app
from app.training.ai_generator import generate


@celery_app.task(name="training.ai_generate")
def ai_generate(plan: dict) -> dict:
    return generate(plan)
