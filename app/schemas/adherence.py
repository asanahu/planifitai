from datetime import date

from pydantic import BaseModel


class AdherenceResponse(BaseModel):
    routine_id: int
    week_start: date
    week_end: date
    planned: int
    completed: int
    adherence_pct: int
    status: str
