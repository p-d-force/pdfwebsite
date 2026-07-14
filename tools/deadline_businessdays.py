from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    d = d + timedelta(days=offset + (n - 1) * 7)
    return d


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def observed_holiday(d: date) -> date:
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def massachusetts_holidays(year: int) -> set[date]:
    holidays = {
        observed_holiday(date(year, 1, 1)),
        nth_weekday(year, 1, 0, 3),
        nth_weekday(year, 2, 0, 3),
        nth_weekday(year, 4, 0, 3),
        last_weekday(year, 5, 0),
        observed_holiday(date(year, 6, 19)),
        observed_holiday(date(year, 7, 4)),
        nth_weekday(year, 9, 0, 1),
        nth_weekday(year, 10, 0, 2),
        observed_holiday(date(year, 11, 11)),
        nth_weekday(year, 11, 3, 4),
        observed_holiday(date(year, 12, 25)),
    }
    return holidays


def holiday_set_for_jurisdiction(jurisdiction: str, year: int) -> set[date]:
    if jurisdiction.upper() == "US-MA":
        return massachusetts_holidays(year)
    return set()


def is_business_day(d: date, jurisdiction: str) -> bool:
    if d.weekday() >= 5:
        return False
    return d not in holiday_set_for_jurisdiction(jurisdiction, d.year)


def business_days_remaining(due: date, today: date, jurisdiction: str) -> int:
    if due == today:
        return 0

    step = 1 if due > today else -1
    cursor = today
    count = 0
    while (step > 0 and cursor <= due) or (step < 0 and cursor >= due):
        if is_business_day(cursor, jurisdiction):
            count += step
        cursor += timedelta(days=step)
    return count


@dataclass
class BusinessDayStatus:
    status: str
    business_days_delta: int
    label: str


def business_day_status(due: date, today: date, jurisdiction: str) -> BusinessDayStatus:
    delta = business_days_remaining(due, today, jurisdiction)
    if delta > 0:
        return BusinessDayStatus(
            status="upcoming",
            business_days_delta=delta,
            label=f"{delta} business day(s) remaining",
        )
    if delta == 0:
        return BusinessDayStatus(status="due-today", business_days_delta=0, label="Due today")
    return BusinessDayStatus(
        status="overdue",
        business_days_delta=delta,
        label=f"{abs(delta)} business day(s) overdue",
    )
