import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models, schemas

logger = logging.getLogger(__name__)


def create_entries(
    db: Session, user_id: int, entries: List[schemas.ProgressEntryCreate]
):
    objs = [
        models.ProgressEntry(user_id=user_id, **entry.model_dump()) for entry in entries
    ]
    db.add_all(objs)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entry already exists for date+metric",
        )
    for obj in objs:
        db.refresh(obj)
    logger.info("Created %s progress entries for user %s", len(objs), user_id)
    return objs


def list_entries(
    db: Session,
    user_id: int,
    metric: Optional[models.MetricEnum] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start > end",
        )
    query = db.query(models.ProgressEntry).filter(
        models.ProgressEntry.user_id == user_id
    )
    if metric:
        query = query.filter(models.ProgressEntry.metric == metric)
    if start:
        query = query.filter(models.ProgressEntry.date >= start)
    if end:
        query = query.filter(models.ProgressEntry.date <= end)
    return query.order_by(models.ProgressEntry.date.asc()).all()


def summary(
    db: Session,
    user_id: int,
    metric: models.MetricEnum,
    start: Optional[date] = None,
    end: Optional[date] = None,
    window_days: Optional[int] = None,
):
    if window_days:
        end = end or date.today()
        start = start or end - timedelta(days=window_days)
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start > end",
        )
    entries = list_entries(db, user_id, metric, start, end)
    count = len(entries)
    if count == 0:
        return schemas.ProgressSummary(
            metric=metric,
            count=0,
            min=None,
            max=None,
            avg=None,
            first=None,
            last=None,
            delta=None,
            start=start,
            end=end,
        )
    values = [e.value for e in entries]
    first_val = values[0]
    last_val = values[-1]
    return schemas.ProgressSummary(
        metric=metric,
        count=count,
        min=min(values),
        max=max(values),
        avg=sum(values) / count,
        first=first_val,
        last=last_val,
        delta=last_val - first_val,
        start=start or entries[0].date,
        end=end or entries[-1].date,
    )


def delete_entry(db: Session, user_id: int, entry_id: int):
    entry = (
        db.query(models.ProgressEntry)
        .filter(
            models.ProgressEntry.id == entry_id,
            models.ProgressEntry.user_id == user_id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )
    db.delete(entry)
    db.commit()
    logger.info("Deleted progress entry %s for user %s", entry_id, user_id)
