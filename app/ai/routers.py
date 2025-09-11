"""FastAPI routers exposing AI functionality."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai_client import get_ai_client
from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db

from . import schemas, services

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/echo")
def echo() -> dict:
    client = get_ai_client()
    client.chat(0, [{"role": "user", "content": "ping"}], simulate=True)
    return {"message": "ok"}


@router.post("/generate/workout-plan", response_model=schemas.WorkoutPlan)
def generate_workout_plan(
    payload: schemas.WorkoutPlanRequest,
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return services.generate_workout_plan(current_user, payload, db=db, simulate=simulate)


@router.post("/generate/nutrition-plan", response_model=schemas.NutritionPlan)
def generate_nutrition_plan(
    payload: schemas.NutritionPlanRequest,
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return services.generate_nutrition_plan(current_user, payload, db=db, simulate=simulate)


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(
    payload: schemas.ChatRequest,
    current_user: UserContext = Depends(get_current_user),
):
    return services.chat(current_user, payload)


@router.post("/insights", response_model=schemas.InsightsResponse)
def insights(
    payload: schemas.InsightsRequest,
    current_user: UserContext = Depends(get_current_user),
):
    return services.insights(current_user, payload)


@router.post("/recommend", response_model=schemas.RecommendResponse)
def recommend(
    payload: schemas.RecommendRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return services.recommend(current_user, payload, db)
