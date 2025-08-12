from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

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
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    full_name = Column(String, index=True)
    age = Column(Integer)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    activity_level = Column(Enum(ActivityLevel))
    goal = Column(Enum(Goal))

    user = relationship("User", back_populates="profile")