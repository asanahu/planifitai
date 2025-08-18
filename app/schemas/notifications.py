from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class WeighInScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_of_week: int = Field(6, ge=0, le=6)
    local_time: str = Field("09:00", pattern=r"^\d{2}:\d{2}$")
    weeks_ahead: int = Field(8, ge=1, le=26)


class WeighInScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    scheduled_count: int
    first_scheduled_local: str | None
    timezone: str
