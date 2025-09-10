from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
try:
    # Pydantic v2: AliasChoices allows multiple aliases
    from pydantic import AliasChoices  # type: ignore
except Exception:  # pragma: no cover
    AliasChoices = None  # type: ignore


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int | str
    name: str = Field(description="Nombre del ejercicio", examples=["Push Up"])
    description: Optional[str] = Field(default=None, description="Descripción corta")
    muscle_groups: List[str] = Field(
        default_factory=list,
        validation_alias=(AliasChoices("muscle_groups", "category") if AliasChoices else "category"),
        description="Grupo(s) muscular(es)",
        examples=[["chest", "triceps"]],
    )
    equipment: Optional[str] = Field(
        default=None, description="Equipo requerido", examples=["bodyweight"]
    )
    level: Optional[str] = Field(
        default=None,
        validation_alias=(AliasChoices("level", "description") if AliasChoices else "description"),
        description="Nivel de dificultad",
        examples=["beginner"],
    )
    pattern: Optional[str] = Field(
        default=None, description="Patrón de movimiento", examples=["push"]
    )
    demo_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL demo",
        examples=["https://example.com/demo"],
    )

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
