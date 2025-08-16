from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import MealType, ServingUnit, TargetSource, WaterSource


class MealItemBase(BaseModel):
    food_id: int | None = None
    food_name: str | None = None
    serving_qty: Decimal = Field(gt=0)
    serving_unit: ServingUnit
    calories_kcal: Decimal = Field(ge=0)
    protein_g: Decimal = Field(ge=0)
    carbs_g: Decimal = Field(ge=0)
    fat_g: Decimal = Field(ge=0)
    fiber_g: Decimal | None = Field(default=None, ge=0)
    sugar_g: Decimal | None = Field(default=None, ge=0)
    sodium_mg: Decimal | None = Field(default=None, ge=0)
    order_index: int | None = None

    @field_validator("food_name")
    @classmethod
    def food_name_required(cls, v, info):
        if info.data.get("food_id") is None and (v is None or v == ""):
            raise ValueError("food_name required when food_id is null")
        return v

    model_config = ConfigDict(from_attributes=True)


class MealItemCreate(MealItemBase):
    pass


class MealItemUpdate(BaseModel):
    food_id: int | None = None
    food_name: str | None = None
    serving_qty: Decimal | None = Field(default=None, gt=0)
    serving_unit: ServingUnit | None = None
    calories_kcal: Decimal | None = Field(default=None, ge=0)
    protein_g: Decimal | None = Field(default=None, ge=0)
    carbs_g: Decimal | None = Field(default=None, ge=0)
    fat_g: Decimal | None = Field(default=None, ge=0)
    fiber_g: Decimal | None = Field(default=None, ge=0)
    sugar_g: Decimal | None = Field(default=None, ge=0)
    sodium_mg: Decimal | None = Field(default=None, ge=0)
    order_index: int | None = None


class MealItemRead(MealItemBase):
    id: int


class MealBase(BaseModel):
    date: date
    meal_type: MealType
    name: str | None = None
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MealCreate(MealBase):
    items: List[MealItemCreate] = []


class MealUpdate(BaseModel):
    meal_type: MealType | None = None
    name: str | None = None
    notes: str | None = None


class MealRead(MealBase):
    id: int
    items: List[MealItemRead] = []


class WaterLogCreate(BaseModel):
    datetime_utc: datetime
    volume_ml: int = Field(gt=0)
    source: WaterSource | None = None


class WaterLogRead(WaterLogCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TargetsAutoParams(BaseModel):
    protein_per_kg: float = 1.8
    fat_ratio: float = 0.3


class TargetsRead(BaseModel):
    date: date
    calories_target: int
    protein_g_target: Decimal
    carbs_g_target: Decimal
    fat_g_target: Decimal
    source: TargetSource
    method: Dict | None = None

    model_config = ConfigDict(from_attributes=True)


class TargetsSetCustom(BaseModel):
    date: date
    calories_target: int
    protein_g_target: Decimal
    carbs_g_target: Decimal
    fat_g_target: Decimal


class MacroTotals(BaseModel):
    calories_kcal: Decimal = Decimal(0)
    protein_g: Decimal = Decimal(0)
    carbs_g: Decimal = Decimal(0)
    fat_g: Decimal = Decimal(0)


class DayLogRead(BaseModel):
    date: date
    meals: List[MealRead]
    totals: MacroTotals
    water_total_ml: int
    targets: TargetsRead | None
    adherence: Dict[str, float] | None = None


class SummaryRead(BaseModel):
    start: date
    end: date
    days: int
    totals: MacroTotals
    average: MacroTotals
    adherence: Dict[str, float] | None = None
