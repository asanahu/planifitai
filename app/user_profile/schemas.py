from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.user_profile.models import ActivityLevel, Goal


class UserProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=50)
    age: Optional[int] = Field(None, gt=0, lt=120)
    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    medical_conditions: Optional[str] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None


class UserProfileCreate(UserProfileBase):
    full_name: str = Field(min_length=2, max_length=50)
    age: int = Field(gt=0, lt=120)
    height_cm: float = Field(gt=0, lt=300)
    weight_kg: float = Field(gt=0, lt=500)
    activity_level: ActivityLevel
    goal: Goal


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# === API modelos específicos para /users/me ===

class MeProfileOut(BaseModel):
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    goal: str | None = None
    activity_level: str | None = None
    profile_completed: bool


class MeProfileIn(BaseModel):
    age: int = Field(ge=14, le=100)
    height_cm: int = Field(ge=120, le=220)
    weight_kg: float = Field(ge=30, le=300)
    goal: str = Field(pattern=r"^(lose_weight|maintain|gain_muscle)$")
    activity_level: str = Field(pattern=r"^(sedentary|light|moderate|active|very_active)$")