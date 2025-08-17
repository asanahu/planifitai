from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import PLAN_NOT_FOUND, err, ok
from app.routines.models import Routine, RoutineDay, RoutineExercise
from app.training import planner

router = APIRouter(prefix="/training", tags=["training"])


class TrainingRequest(BaseModel):
    objective: str
    level: str
    frequency: int
    session_minutes: int
    restrictions: list[str] = []
    persist: bool = False
    use_ai: bool = False


@router.post("/generate")
def generate_training(payload: TrainingRequest, db: Session = Depends(get_db)):
    try:
        plan = planner.generate_plan_v2(
            payload.objective,
            payload.level,
            payload.frequency,
            payload.session_minutes,
            payload.restrictions,
            payload.use_ai,
        )
    except ValueError as exc:
        message = str(exc).split(":", 1)[-1].strip()
        return err("PLAN_INVALID_FREQ", message)
    except KeyError:
        return err(PLAN_NOT_FOUND, "Plantilla no encontrada", 404)

    if payload.persist:
        routine = Routine(name=f"{payload.objective} plan", description=None)
        db.add(routine)
        db.flush()
        for dp in plan.days:
            day = RoutineDay(
                routine_id=routine.id, weekday=dp.day - 1, order_index=dp.day - 1
            )
            db.add(day)
            db.flush()
            for idx, block in enumerate(dp.blocks):
                for order, ex in enumerate(block.exercises):
                    db.add(
                        RoutineExercise(
                            routine_day_id=day.id,
                            exercise_name=ex.name,
                            sets=ex.sets or 1,
                            reps=ex.reps,
                            time_seconds=ex.seconds,
                            order_index=order,
                        )
                    )
        db.commit()
        return ok({"routine_id": routine.id, "plan": plan.model_dump()})

    return ok(plan.model_dump())
