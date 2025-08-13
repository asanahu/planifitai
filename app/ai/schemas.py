from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel


# --- Workout plan -----------------------------------------------------------

class WorkoutExercise(BaseModel):
    name: str
    sets: int
    reps: int
    rest_sec: Optional[int] = None
    notes: Optional[str] = None


class WorkoutPlanDay(BaseModel):
    weekday: str
    focus: Optional[str] = None
    exercises: List[WorkoutExercise]


class WorkoutPlan(BaseModel):
    name: str
    days_per_week: int
    days: List[WorkoutPlanDay]
    constraints: Optional[Dict[str, str]] = None
    total_time_min: Optional[int] = None


class WorkoutPlanRequest(BaseModel):
    days_per_week: int
    equipment: Optional[str] = None
    preferences: Optional[Dict[str, str]] = None


# --- Nutrition plan ---------------------------------------------------------

class MealItem(BaseModel):
    name: str
    qty: float
    unit: str
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


class Meal(BaseModel):
    type: Literal["breakfast", "lunch", "dinner", "snack"]
    items: List[MealItem]
    meal_kcal: float


class NutritionDayPlan(BaseModel):
    date: str
    meals: List[Meal]
    totals: Dict[str, float]


class NutritionPlan(BaseModel):
    days: List[NutritionDayPlan]
    targets: Dict[str, float]


class NutritionPlanRequest(BaseModel):
    days: int
    preferences: Optional[Dict[str, str]] = None


# --- Chat -------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    tools_allowed: Optional[bool] = False
    simulate: Optional[bool] = False


class ChatResponse(BaseModel):
    reply: str
    actions: Optional[List[str]] = None


# --- Insights ---------------------------------------------------------------

class InsightsRequest(BaseModel):
    date_from: str
    date_to: str
    goal: str


class InsightsResponse(BaseModel):
    trends: Dict[str, Dict[str, float | bool]]
    predictions: Optional[Dict[str, str]] = None
    suggestions: List[str]


# --- Recommendations --------------------------------------------------------

class RecommendRequest(BaseModel):
    namespace: str
    ref_id: str
    k: int = 5


class RecommendItem(BaseModel):
    ref_id: str
    title: str
    score: float
    metadata: Optional[Dict[str, str]] = None


class RecommendResponse(BaseModel):
    items: List[RecommendItem]
