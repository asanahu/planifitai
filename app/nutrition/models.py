import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    other = "other"


class ServingUnit(str, enum.Enum):
    g = "g"
    ml = "ml"
    unit = "unit"


class WaterSource(str, enum.Enum):
    manual = "manual"
    app = "app"
    wearable = "wearable"


class TargetSource(str, enum.Enum):
    auto = "auto"
    custom = "custom"


class NutritionMeal(Base):
    __tablename__ = "nutrition_meals"
    __table_args__ = (Index("ix_nutrition_meals_user_date", "user_id", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    meal_type = Column(SqlEnum(MealType, name="mealtype"), nullable=False)
    name = Column(String(255), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items = relationship(
        "NutritionMealItem",
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="NutritionMealItem.order_index",
    )


class NutritionMealItem(Base):
    __tablename__ = "nutrition_meal_items"
    __table_args__ = (
        CheckConstraint("serving_qty > 0", name="ck_meal_item_serving_qty_positive"),
        CheckConstraint("calories_kcal >= 0", name="ck_item_calories_nonneg"),
        CheckConstraint("protein_g >= 0", name="ck_item_protein_nonneg"),
        CheckConstraint("carbs_g >= 0", name="ck_item_carbs_nonneg"),
        CheckConstraint("fat_g >= 0", name="ck_item_fat_nonneg"),
    )

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(
        Integer,
        ForeignKey("nutrition_meals.id", ondelete="CASCADE"),
        nullable=False,
    )
    food_id = Column(Integer, nullable=True)
    food_name = Column(String(255), nullable=True)
    serving_qty = Column(Numeric(10, 2), nullable=False)
    serving_unit = Column(SqlEnum(ServingUnit, name="servingunit"), nullable=False)
    calories_kcal = Column(Numeric(10, 2), nullable=False)
    protein_g = Column(Numeric(10, 2), nullable=False)
    carbs_g = Column(Numeric(10, 2), nullable=False)
    fat_g = Column(Numeric(10, 2), nullable=False)
    fiber_g = Column(Numeric(10, 2), nullable=True)
    sugar_g = Column(Numeric(10, 2), nullable=True)
    sodium_mg = Column(Numeric(10, 2), nullable=True)
    order_index = Column(Integer, default=0)

    meal = relationship("NutritionMeal", back_populates="items")


class NutritionWaterLog(Base):
    __tablename__ = "nutrition_water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    datetime_utc = Column(DateTime(timezone=True), nullable=False)
    volume_ml = Column(Integer, nullable=False)
    source = Column(SqlEnum(WaterSource, name="watersource"), nullable=True)


class NutritionTarget(Base):
    __tablename__ = "nutrition_targets"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uix_target_user_date"),
        Index("ix_nutrition_targets_user_date", "user_id", "date"),
        CheckConstraint("calories_target > 0", name="ck_target_calories_positive"),
        CheckConstraint("protein_g_target >= 0", name="ck_target_protein_nonneg"),
        CheckConstraint("carbs_g_target >= 0", name="ck_target_carbs_nonneg"),
        CheckConstraint("fat_g_target >= 0", name="ck_target_fat_nonneg"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    calories_target = Column(Integer, nullable=False)
    protein_g_target = Column(Numeric(10, 2), nullable=False)
    carbs_g_target = Column(Numeric(10, 2), nullable=False)
    fat_g_target = Column(Numeric(10, 2), nullable=False)
    source = Column(SqlEnum(TargetSource, name="targetsource"), nullable=False)
    method = Column(JSON, nullable=True)


class FoodSource(str, enum.Enum):
    fdc = "fdc"
    bedca = "bedca"


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uix_food_source_source_id"),
        Index("ix_food_name", "name"),
    )

    # Store UUID as string for cross-DB compatibility
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)
    source = Column(SqlEnum(FoodSource, name="foodsource"), nullable=False)
    source_id = Column(String(100), nullable=False)

    # canonical per 100 g
    calories_kcal = Column(Numeric(10, 2), nullable=True)
    protein_g = Column(Numeric(10, 2), nullable=True)
    carbs_g = Column(Numeric(10, 2), nullable=True)
    fat_g = Column(Numeric(10, 2), nullable=True)

    portion_suggestions = Column(JSON, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    lang = Column(String(8), nullable=False, default="en")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
