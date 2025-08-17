from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Exercise(BaseModel):
    name: str
    sets: int | None = None
    reps: int | None = None
    seconds: int | None = None


class Block(BaseModel):
    type: Literal["straight", "emom", "for_time"]
    duration: int | None = None
    exercises: list[Exercise]

    @field_validator("exercises")
    @classmethod
    def _validate_straight(cls, v, info):
        block_type = info.data.get("type")
        if block_type == "straight" and len(v) < 2:
            raise ValueError("straight block requires at least two exercises")
        return v


class DayPlan(BaseModel):
    day: int
    blocks: list[Block]

    @field_validator("blocks")
    @classmethod
    def _at_least_one_block(cls, v):
        if len(v) < 1:
            raise ValueError("each day requires at least one block")
        return v


class PlanDTO(BaseModel):
    objective: str
    level: Level
    frequency: int
    session_minutes: int
    days: list[DayPlan]
    meta: dict = {}

    @model_validator(mode="after")
    def _check_frequency(self) -> "PlanDTO":
        if len(self.days) != self.frequency:
            raise ValueError("frequency and number of days mismatch")
        return self
