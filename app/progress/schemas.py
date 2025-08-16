from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, field_validator

from .models import MetricEnum


class ProgressEntryBase(BaseModel):
    date: date
    metric: MetricEnum
    value: float
    unit: str | None = ""
    notes: str | None = None

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float, info):
        metric = info.data.get("metric")
        if metric == MetricEnum.weight and not (30 <= v <= 300):
            raise ValueError("weight must be between 30 and 300")
        if metric == MetricEnum.steps and v < 0:
            raise ValueError("steps must be >= 0")
        if metric == MetricEnum.rhr and not (30 <= v <= 220):
            raise ValueError("rhr must be between 30 and 220")
        if metric == MetricEnum.bodyfat and not (3 <= v <= 70):
            raise ValueError("bodyfat must be between 3 and 70")
        return v


class ProgressEntryCreate(ProgressEntryBase):
    pass


class ProgressEntryCreateBulk(BaseModel):
    items: List[ProgressEntryCreate]


class ProgressEntryRead(ProgressEntryBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class ProgressSummary(BaseModel):
    metric: MetricEnum
    count: int
    min: float | None
    max: float | None
    avg: float | None
    first: float | None
    last: float | None
    delta: float | None
    start: date | None
    end: date | None
