from __future__ import annotations

import logging
import time
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.progress.models import MetricEnum, ProgressEntry
from app.routines.models import Routine
from app.schemas.adherence import AdherenceResponse
from app.utils.datetimes import monday_sunday_bounds, week_bounds

logger = logging.getLogger(__name__)


ALLOWED_RANGES = {"last_week", "this_week", "custom"}


def _normalize_start(day: date) -> date:
    monday, _ = monday_sunday_bounds(day)
    return monday


def compute_weekly_workout_adherence(
    db: Session,
    routine_id: int,
    start: date | None = None,
    range: str = "last_week",
    tz: str = "Europe/Madrid",
) -> AdherenceResponse:
    """Compute weekly workout adherence for a routine."""
    start_ts = time.time()
    if range not in ALLOWED_RANGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid range"
        )

    if range == "custom":
        if start is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start required for custom range",
            )
        week_start, week_end = monday_sunday_bounds(_normalize_start(start), tz)
    else:
        week_start, week_end = week_bounds(range, tz)

    routine = (
        db.query(Routine)
        .filter(Routine.id == routine_id, Routine.deleted_at.is_(None))
        .first()
    )
    if not routine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found"
        )

    active_days = routine.active_days or {}
    weekday_map = {
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
    }
    active_weekdays = {
        idx for name, idx in weekday_map.items() if active_days.get(name)
    }

    planned = 0
    current = week_start
    while current <= week_end:
        wd = current.weekday()
        if wd in active_weekdays:
            if routine.start_date and current < routine.start_date.date():
                pass
            elif routine.end_date and current > routine.end_date.date():
                pass
            else:
                planned += 1
        current += timedelta(days=1)

    completed_dates = (
        db.query(ProgressEntry.date)
        .filter(
            ProgressEntry.user_id == routine.owner_id,
            ProgressEntry.metric == MetricEnum.workout,
            ProgressEntry.date >= week_start,
            ProgressEntry.date <= week_end,
        )
        .all()
    )
    completed = len({d[0] for d in completed_dates})

    pct = round((completed / planned) * 100) if planned > 0 else 0
    status_str = "ok" if planned > 0 else "no_planned"

    duration_ms = int((time.time() - start_ts) * 1000)
    logger.info(
        "routine_adherence",
        extra={
            "routine_id": routine_id,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "planned": planned,
            "completed": completed,
            "pct": pct,
            "duration_ms": duration_ms,
        },
    )

    return AdherenceResponse(
        routine_id=routine_id,
        week_start=week_start,
        week_end=week_end,
        planned=planned,
        completed=completed,
        adherence_pct=pct,
        status=status_str,
    )
