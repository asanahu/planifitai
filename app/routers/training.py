from fastapi import APIRouter
from pydantic import BaseModel

from app.core.errors import PLAN_NOT_FOUND, err, ok
from app.training import planner
from app.training.tasks import ai_generate

router = APIRouter(prefix="/training", tags=["training"])


class TrainingRequest(BaseModel):
    objective: str
    frequency: int
    restrictions: list[str] = []


@router.post("/generate")
def generate_training(payload: TrainingRequest):
    try:
        plan = planner.generate_plan(
            payload.objective, payload.frequency, payload.restrictions
        )
    except ValueError as exc:
        message = str(exc).split(":", 1)[-1].strip()
        return err("PLAN_INVALID_FREQ", message)
    except KeyError:
        return err(PLAN_NOT_FOUND, "Plantilla no encontrada", 404)

    result = ai_generate.apply(args=[plan]).get()
    return ok(result)
