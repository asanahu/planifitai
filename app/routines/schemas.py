from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# Schemas for ExerciseCatalog
class ExerciseCatalogBase(BaseModel):
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    equipment: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)


class ExerciseCatalogCreate(ExerciseCatalogBase):
    pass


class ExerciseCatalogUpdate(ExerciseCatalogBase):
    pass


class ExerciseCatalogRead(ExerciseCatalogBase):
    id: int

    class Config:
        orm_mode = True


# Schemas for RoutineExercise
class RoutineExerciseBase(BaseModel):
    exercise_name: str = Field(..., max_length=100)
    sets: int
    reps: Optional[int] = None
    time_seconds: Optional[int] = None
    tempo: Optional[str] = Field(None, max_length=20)
    rest_seconds: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=2000)
    order_index: int = 0


class RoutineExerciseCreate(RoutineExerciseBase):
    exercise_id: Optional[int] = None


class RoutineExerciseUpdate(RoutineExerciseBase):
    exercise_id: Optional[int] = None


class RoutineExerciseRead(RoutineExerciseBase):
    id: int
    exercise_id: Optional[int] = None

    class Config:
        orm_mode = True


# Schemas for RoutineDay
class RoutineDayBase(BaseModel):
    weekday: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    order_index: int = 0


class RoutineDayCreate(RoutineDayBase):
    exercises: List[RoutineExerciseCreate] = []


class RoutineDayUpdate(RoutineDayBase):
    exercises: List[RoutineExerciseUpdate] = []


class RoutineDayRead(RoutineDayBase):
    id: int
    exercises: List[RoutineExerciseRead] = []

    class Config:
        orm_mode = True


# Schemas for Routine
class RoutineBase(BaseModel):
    name: str = Field(..., max_length=80)
    description: Optional[str] = Field(None, max_length=2000)
    is_template: bool = False
    is_public: bool = False
    active_days: Optional[Dict[str, bool]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class RoutineCreate(RoutineBase):
    days: List[RoutineDayCreate] = []


class RoutineUpdate(RoutineBase):
    pass


class RoutineRead(RoutineBase):
    id: int
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    days: List[RoutineDayRead] = []

    class Config:
        orm_mode = True


# Schemas for cloning a template
class CloneFromTemplateRequest(BaseModel):
    template_id: int


# Schemas for completing an exercise
class CompleteExerciseRequest(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[int] = None


class ScheduleNotificationsRequest(BaseModel):
    hour: Optional[int] = None
