from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def monday_sunday_bounds(day: date, tz: str = "Europe/Madrid") -> tuple[date, date]:
    """Return Monday-Sunday date bounds for the week containing ``day``.

    The ``day`` is interpreted in the provided ``tz`` timezone. Returned dates are
    naive ``date`` objects representing the start (Monday) and end (Sunday) of the
    week.
    """
    # Weekday: Monday=0 ... Sunday=6
    weekday = day.weekday()
    monday = day - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def week_bounds(range: str, tz: str = "Europe/Madrid") -> tuple[date, date]:
    """Return date bounds for ``range`` relative to "today" in ``tz``.

    ``range`` accepts ``last_week`` or ``this_week``.
    """
    today = datetime.now(ZoneInfo(tz)).date()
    if range == "this_week":
        return monday_sunday_bounds(today, tz)
    if range == "last_week":
        this_monday, _ = monday_sunday_bounds(today, tz)
        last_monday = this_monday - timedelta(days=7)
        return monday_sunday_bounds(last_monday, tz)
    raise ValueError("invalid range")
