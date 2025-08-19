from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int | str
    name: str
    muscle_groups: List[str] = Field(
        default_factory=list,
        validation_alias="category",
        description="Grupo(s) muscular(es)",
    )
    equipment: Optional[str] = None
    level: Optional[str] = Field(default=None, validation_alias="description")
    pattern: Optional[str] = None
    demo_url: Optional[HttpUrl] = None

    @field_validator("muscle_groups", mode="before")
    @classmethod
    def _split_muscles(cls, v: object) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [m.strip() for m in v.split(",") if m.strip()]
        if isinstance(v, list):
            return v
        return []


class ExerciseCatalogResponse(BaseModel):
    items: list[ExerciseRead]
    total: int
    limit: int
    offset: int
