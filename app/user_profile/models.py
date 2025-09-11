import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.security.types import EncryptedFloat, EncryptedString


class ActivityLevel(str, enum.Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class Goal(str, enum.Enum):
    LOSE_WEIGHT = "lose_weight"
    MAINTAIN_WEIGHT = "maintain_weight"
    GAIN_WEIGHT = "gain_weight"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False
    )
    full_name = Column(String, index=True)
    # New granular identity fields
    first_name = Column(String, index=True, nullable=True)
    last_name = Column(String, index=True, nullable=True)
    sex = Column(String(16), nullable=True)  # male|female|other
    age = Column(Integer)
    height_cm = Column(EncryptedFloat)
    weight_kg = Column(EncryptedFloat)
    medical_conditions = Column(EncryptedString, nullable=True)
    # Training and planning preferences
    training_days_per_week = Column(Integer, nullable=True)
    time_per_session_min = Column(Integer, nullable=True)
    equipment_access = Column(String(32), nullable=True)  # none|basic|full_gym
    dietary_preference = Column(String(32), nullable=True)  # omnivore|vegetarian|vegan|...
    allergies = Column(EncryptedString, nullable=True)
    activity_level = Column(Enum(ActivityLevel))
    goal = Column(Enum(Goal))
    profile_completed = Column(Boolean, nullable=False, server_default="0")

    user = relationship("User", back_populates="profile")
