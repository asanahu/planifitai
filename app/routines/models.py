
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    is_template = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    active_days = Column(JSON, nullable=True)  # e.g., {"mon": true, "tue": false, ...}
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    owner = relationship("User")
    days = relationship("RoutineDay", back_populates="routine", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('owner_id', 'name', name='_owner_name_uc'),
    )

class RoutineDay(Base):
    __tablename__ = "routine_days"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    order_index = Column(Integer, default=0, nullable=False)

    routine = relationship("Routine", back_populates="days")
    exercises = relationship("RoutineExercise", back_populates="day", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('routine_id', 'weekday', name='_routine_weekday_uc'),
    )


class ExerciseCatalog(Base):
    __tablename__ = "exercise_catalog"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)
    equipment = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)


class RoutineExercise(Base):
    __tablename__ = "routine_exercises"

    id = Column(Integer, primary_key=True, index=True)
    routine_day_id = Column(Integer, ForeignKey("routine_days.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercise_catalog.id"), nullable=True)
    exercise_name = Column(String(100), nullable=False) # Denormalized for simplicity, or if no catalog entry
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=True)
    time_seconds = Column(Integer, nullable=True)
    tempo = Column(String(20), nullable=True)
    rest_seconds = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)

    day = relationship("RoutineDay", back_populates="exercises")
    exercise = relationship("ExerciseCatalog")
