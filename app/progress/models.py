import enum
from sqlalchemy import Column, Integer, ForeignKey, Date, Float, String, UniqueConstraint, Index, Enum as SqlEnum
from app.core.database import Base


class MetricEnum(str, enum.Enum):
    weight = "weight"
    steps = "steps"
    rhr = "rhr"
    bodyfat = "bodyfat"
    workout = "workout"


class ProgressEntry(Base):
    __tablename__ = "progress_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "date", "metric", name="uix_user_date_metric"),
        Index("ix_progress_user_metric_date", "user_id", "metric", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    metric = Column(SqlEnum(MetricEnum, name="progressmetric"), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(16), default="", nullable=True)
    notes = Column(String(255), nullable=True)
