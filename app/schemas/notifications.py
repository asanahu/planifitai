from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class WeighInScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_of_week: int = Field(
        6,
        ge=0,
        le=6,
        description="Day of week for the reminder (0=Monday, 6=Sunday)",
        examples=[6],
    )
    local_time: str = Field(
        "09:00",
        pattern=r"^\d{2}:\d{2}$",
        description="Local time in HH:MM when the reminder should fire",
        examples=["09:00"],
    )
    weeks_ahead: int = Field(
        8,
        ge=1,
        le=26,
        description="Number of upcoming weeks to schedule (1-26)",
        examples=[8],
    )


class WeighInScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    scheduled_count: int = Field(
        ..., description="Total notifications scheduled", examples=[8]
    )
    first_scheduled_local: str | None = Field(
        None,
        description="ISO 8601 timestamp of the first notification in local time",
        examples=["2024-08-19T09:00:00+02:00"],
    )
    timezone: str = Field(
        ..., description="IANA timezone used for scheduling", examples=["Europe/Madrid"]
    )
