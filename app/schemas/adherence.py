from datetime import date

from pydantic import BaseModel, Field


class AdherenceResponse(BaseModel):
    routine_id: int = Field(..., description="ID of the routine", examples=[123])
    week_start: date = Field(
        ..., description="Start date of the analysed week", examples=["2024-08-05"]
    )
    week_end: date = Field(
        ..., description="End date of the analysed week", examples=["2024-08-11"]
    )
    planned: int = Field(
        ..., description="Number of planned workouts for the period", examples=[4]
    )
    completed: int = Field(
        ..., description="Workouts completed in the period", examples=[3]
    )
    adherence_pct: int = Field(
        ..., description="Completion percentage (0-100)", examples=[75]
    )
    status: str = Field(..., description="Adherence status label", examples=["good"])
